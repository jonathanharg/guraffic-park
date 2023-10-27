import pygame

# import the scene class
from cubeMap import FlattenCubeMap
from scene import Scene

from lightSource import LightSource

from blender import load_obj_file

from BaseModel import DrawModelFromMesh

from shaders import *

from ShadowMapping import *

from sphereModel import Sphere

from skyBox import *

from environmentMapping import *

class ExeterScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.light = LightSource(self, position=[3., 4., -3.])

        self.shaders='phong'

        # for shadow map rendering
        self.shadows = ShadowMap(light=self.light)
        self.show_shadow_map = ShowTexture(self, self.shadows)

        meshes = load_obj_file('models/scene.obj')
        self.add_models_list(
            [DrawModelFromMesh(scene=self, M=np.matmul(translationMatrix([0,-1,0]),scaleMatrix([0.5,0.5,0.5])), mesh=mesh, shader=ShadowMappingShader(shadow_map=self.shadows), name='scene') for mesh in meshes]
        )

        table = load_obj_file('models/quad_table.obj')
        self.table = [DrawModelFromMesh(scene=self, M=translationMatrix([0, -4, +0]), mesh=mesh, shader=ShadowMappingShader(shadow_map=self.shadows), name='table') for mesh in table]

        box = load_obj_file('models/fluid_border.obj')
        self.box = [DrawModelFromMesh(scene=self, M=translationMatrix([0,0,0]), mesh=mesh, shader=self.shaders, name='box') for mesh in box]

        # draw a skybox for the horizon
        self.skybox = SkyBox(scene=self)

        self.show_light = DrawModelFromMesh(scene=self, M=poseMatrix(position=self.light.position, scale=0.2), mesh=Sphere(material=Material(Ka=[10,10,10])), shader=FlatShader())

        self.environment = EnvironmentMappingTexture(width=400, height=400)

        self.sphere = DrawModelFromMesh(scene=self, M=poseMatrix(), mesh=Sphere(), shader=EnvironmentShader(map=self.environment))
        #self.sphere = DrawModelFromMesh(scene=self, M=poseMatrix(), mesh=Sphere(), shader=FlatShader())

        bunny = load_obj_file('models/bunny_world.obj')
        self.bunny = DrawModelFromMesh(scene=self, M=np.matmul(translationMatrix([0,0,0]), scaleMatrix([0.5,0.5,0.5])), mesh=bunny[0], shader=EnvironmentShader(map=self.environment))

        # environment box for reflections
        #self.envbox = EnvironmentBox(scene=self)

        # this object allows to visualise the flattened cube

        #self.flattened_cube = FlattenCubeMap(scene=self, cube=CubeMap(name='skybox/ame_ash'))
        self.flattened_cube = FlattenCubeMap(scene=self, cube=self.environment)

        self.show_texture = ShowTexture(self, Texture('lena.bmp'))

    def draw_shadow_map(self):
        # first we need to clear the scene, we also clear the depth buffer to handle occlusions
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # also all models from the table
        for model in self.table:
            model.draw()

        # and for the box
        for model in self.box:
            model.draw()

    def draw_reflections(self):
        self.skybox.draw()

        for model in self.models:
            model.draw()

        # also all models from the table
        for model in self.table:
            model.draw()

        # and for the box
        for model in self.box:
            model.draw()


    def draw(self, framebuffer=False):
        '''
        Draw all models in the scene
        :return: None
        '''

        # first we need to clear the scene, we also clear the depth buffer to handle occlusions
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # when using a framebuffer, we do not update the camera to allow for arbitrary viewpoint.
        if not framebuffer:
            self.camera.update()

        # first, we draw the skybox
        self.skybox.draw()

        # render the shadows
        self.shadows.render(self)

        # when rendering the framebuffer we ignore the reflective object
        if not framebuffer:
            #glEnable(GL_BLEND)
            #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
#            self.envbox.draw()
            #self.environment.update(self)
            #self.envbox.draw()

            self.environment.update(self)

            self.bunny.draw()
            #self.sphere.draw()
            #glDisable(GL_BLEND)

            # if enabled, show flattened cube
            self.flattened_cube.draw()

            # if enabled, show texture
            self.show_texture.draw()

            self.show_shadow_map.draw()

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

        # also all models from the table
        for model in self.table:
            model.draw()

        # and for the box
        for model in self.box:
            model.draw()

        self.show_light.draw()

        # once we are done drawing, we display the scene
        # Note that here we use double buffering to avoid artefacts:
        # we draw on a different buffer than the one we display,
        # and flip the two buffers once we are done drawing.
        if not framebuffer:
            pygame.display.flip()

    def keyboard(self, event):
        '''
        Process additional keyboard events for this demo.
        '''
        Scene.keyboard(self, event)

        if event.key == pygame.K_c:
            if self.flattened_cube.visible:
                self.flattened_cube.visible = False
            else:
                print('--> showing cube map')
                self.flattened_cube.visible = True

        if event.key == pygame.K_t:
            if self.show_texture.visible:
                self.show_texture.visible = False
            else:
                print('--> showing texture map')
                self.show_texture.visible = True

        if event.key == pygame.K_s:
            if self.show_shadow_map.visible:
                self.show_shadow_map.visible = False
            else:
                print('--> showing shadow map')
                self.show_shadow_map.visible = True

        if event.key == pygame.K_1:
            print('--> using Flat shading')
            self.bunny.use_textures = True
            self.bunny.bind_shader('flat')

        if event.key == pygame.K_2:
            print('--> using Phong shading')
            self.bunny.use_textures = True
            self.bunny.bind_shader('phong')

        elif event.key == pygame.K_4:
            print('--> using original texture')
            self.bunny.shader.mode = 1

        elif event.key == pygame.K_6:
            self.bunny.mesh.material.alpha += 0.1
            print('--> bunny alpha={}'.format(self.bunny.mesh.material.alpha))
            if self.bunny.mesh.material.alpha > 1.0:
                self.bunny.mesh.material.alpha = 0.0

        elif event.key == pygame.K_7:
            print('--> no face culling')
            glDisable(GL_CULL_FACE)

        elif event.key == pygame.K_8:
            print('--> glCullFace(GL_FRONT)')
            glEnable(GL_CULL_FACE)
            glCullFace(GL_FRONT)

        elif event.key == pygame.K_9:
            print('--> glCullFace(GL_BACK)')
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)

        elif event.key == pygame.K_BACKQUOTE:
            if glIsEnabled(GL_DEPTH_TEST):
                print('--> disable GL_DEPTH_TEST')
                glDisable(GL_DEPTH_TEST)
            else:
                print('--> enable GL_DEPTH_TEST')
                glEnable(GL_DEPTH_TEST)


if __name__ == '__main__':
    # initialises the scene object
    # scene = Scene(shaders='gouraud')
    scene = ExeterScene()

    # starts drawing the scene
    scene.run()
