import imgui
import pygame
import quaternion
from OpenGL import GL as gl

from camera import Camera, NoclipCamera
from lightSource import LightSource
from model import Model
from scene import Scene


class MainScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.light = LightSource(self, position=[5.0, 3.0, 5.0])

        # ldn = load_obj_file("models/london.obj")
        # self.add_models_list([DrawModelFromMesh(scene=self, M=translationMatrix([0,0,0]),mesh=mesh,shader=FlatShader(),) for mesh in ldn])
        # Model.from_obj("london.obj")

        self.camera = NoclipCamera()

        floor = Model.from_obj("scene.obj", scale=0.5)
        table = Model.from_obj(
            "quad_table.obj", position=(0, -3, 0), scale=2.0, parent=floor
        )
        Model.from_obj(
            "bunny_world.obj", position=(0, 1, -10), scale=0.5, parent=self.camera
        )
        self.box = Model.from_obj("fluid_border.obj", position=(0, 1, 0))
        Model.from_obj(
            "bunny_world.obj", position=(0, 3, 0), scale=0.5, parent=self.box
        )
        # self.camera.parent = self.box

    def keyboard(self, event):
        """
        Process additional keyboard events for this demo.
        """
        Scene.keyboard(self, event)

        if event.key == pygame.K_1:
            print("Number 1 detected")

        #     print("--> using Flat shading")
        #     self.bunny.use_textures = True
        #     self.bunny.bind_shader("flat")

        # elif event.key == pygame.K_2:
        #     print("--> using Texture shading")
        #     self.bunny.bind_shader("texture")

    def draw(self):
        """
        Draw all models in the scene
        :return: None
        """
        self.camera.update()

        self.box.rotation = (
            quaternion.from_rotation_vector([self.delta_time, 0, 0]) * self.box.rotation
        )

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

        if self.show_imgui_demo:
            self.show_imgui_demo = imgui.show_demo_window(True)

        with imgui.begin("Scene", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE):
            imgui.text("Press ESC to interact with the menu")
            imgui.text(f"FPS: {self.clock.get_fps():.2f}")
            imgui.text(f"Frametime: {self.clock.get_time():.2f}ms")

            (fov_changed, self.fov) = imgui.slider_float("FOV", self.fov, 30, 150)
            if fov_changed:
                self.update_viewport()

            _, self.fps_max = imgui.slider_float("Max FPS", self.fps_max, 15, 600)

            _, self.wireframe = imgui.checkbox("Wireframe", self.wireframe)
            if self.wireframe:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            else:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

            clicked_noclip_checkbox, self.noclip = imgui.checkbox("Noclip", self.noclip)
            if clicked_noclip_checkbox:
                if self.noclip:
                    self.camera = NoclipCamera(self)
                else:
                    self.camera = Camera()

            imgui.separator()
            if imgui.tree_node("Models"):
                for model in self.models:
                    if imgui.tree_node(model.name):
                        model.debug_menu()
                        imgui.tree_pop()
                imgui.tree_pop()
            imgui.separator()

            if imgui.tree_node("Camera"):
                self.camera.debug_menu()
                imgui.tree_pop()

            if imgui.button("Open ImGui Demo"):
                self.show_imgui_demo = True

            if imgui.button("Quit"):
                self.running = False


if __name__ == "__main__":
    # initialises the scene object
    # scene = Scene(shaders='gouraud')
    scene = MainScene()

    # starts drawing the scene
    scene.run()
