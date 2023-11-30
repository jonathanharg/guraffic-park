import cProfile
import pstats

import imgui
import numpy as np
import pygame
import quaternion
from OpenGL import GL as gl

from camera import Camera, FreeCamera, OrbitCamera
from environment_mapping import EnvironmentMappingTexture
from model import Model
from scene import Scene
from shaders import EnvironmentShader, NewShader
from shadow_mapping import ShadowMap
from skybox import SkyBox


class MainScene(Scene):
    def __init__(self):
        Scene.__init__(self)
        self.light.position = (-0.2, -1.0, -0.3)

        # cube = Model()
        self.orbit_camera = OrbitCamera()
        self.free_camera = FreeCamera()
        self.reflection_camera = Camera(position=(35, 5, -45))
        self.camera = self.orbit_camera
        self.environment = EnvironmentMappingTexture(
            self.reflection_camera, width=400, height=400
        )

        self.skybox = SkyBox()
        self.shadows = ShadowMap(light=self.light)
        # self.cube = Model.from_obj("colour_cube.obj", position=(-5, 2, -5))

        self.london = Model.from_obj("london.obj", shader=NewShader())
        Model.from_obj("shard.obj", shader=EnvironmentShader())
        Model.from_obj(
            "colour_cube.obj", position=(35, 5, -45), shader=EnvironmentShader()
        )

        self.dino = Model.from_obj(
            "dino_body.obj",
            rotation=quaternion.from_rotation_vector((0, np.pi, 0)),
            scale=0.3,
        )
        self.dino_left_wing = Model.from_obj(
            "dino_left.obj", position=(2.5, 0, 2), parent=self.dino
        )
        self.dino_right_wing = Model.from_obj(
            "dino_right.obj", position=(-2.5, 0, 2), parent=self.dino
        )

    def run(self):
        # self.box.rotation = (
        #     quaternion.from_rotation_vector([self.delta_time, 0, 0]) * self.box.rotation
        # )

        wing_resting_pose = np.quaternion(1.0, 0.0, 0.0, 0.0)
        left_wing_down_pose = quaternion.from_rotation_vector((0, 0, -np.pi / 4))
        right_wing_down_pose = quaternion.from_rotation_vector((0, 0, np.pi / 4))

        flap_start = 0
        flap_end = 1000  # Take this many milliseconds to rotate
        t = 500 * np.cos((np.pi / 1000) * pygame.time.get_ticks()) + 500

        left_wing_rotation = quaternion.slerp(
            wing_resting_pose, left_wing_down_pose, flap_start, flap_end, t
        )
        right_wing_rotation = quaternion.slerp(
            wing_resting_pose, right_wing_down_pose, flap_start, flap_end, t
        )

        self.dino_left_wing.rotation = left_wing_rotation
        self.dino_right_wing.rotation = right_wing_rotation

        super().run()

    def draw(self):
        """
        Draw all models in the scene
        :return: None
        """
        self.camera.update()
        # self.shadows.render(self)

        # self.draw_shadow_map(self)

        self.environment.update()

        # if self.skybox is not None:
        #     self.skybox.draw()

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

    # def draw_shadow_map(self):
    #     if self.light is not None:
    #         self.P = frustumMatrix(-1.0, +1.0, -1.0, +1.0, 1.0, 20.0)
    #         self.V = lookAt(np.array(self.light.position), np.array(target))
    #         scene.camera.V = self.V

    #         # update the viewport for the image size
    #         gl.glViewport(0, 0, self.width, self.height)

    #         self.fbo.bind()
    #                     # TODO: REMOVE THIS THIS IS TERRIBLE DESIGN
    #         # first we need to clear the scene, we also clear the depth buffer to handle occlusions
    #         gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    #         # also all models from the table
    #         for model in self.models:
    #             model.draw()
    #         self.fbo.unbind()

    #         # reset the viewport to the windows size
    #         gl.glViewport(0, 0, scene.window_size[0], scene.window_size[1])

    #         # restore the view matrix
    #         scene.camera.V = None
    #         scene.camera.update()

    def debug_menu(self):
        with imgui.begin("Scene", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE):
            imgui.text("Press ESC to interact with the menu")
            imgui.text(f"FPS: {self.clock.get_fps():.2f}")
            imgui.text(f"Frametime: {self.clock.get_time():.2f}ms")
            imgui.text(
                f"OpenGL v{gl.glGetIntegerv(gl.GL_MAJOR_VERSION)}.{gl.glGetIntegerv(gl.GL_MINOR_VERSION)}"
            )
            imgui.plot_lines(
                "Frametime", np.array(self.frame_times, dtype=np.float32), scale_min=0.0
            )

            # FOV Slider
            (fov_changed, self.fov) = imgui.slider_float("FOV", self.fov, 30, 150)
            if fov_changed:
                self.update_viewport()

            # Max FPS Slider
            _, self.fps_max = imgui.slider_float("Max FPS", self.fps_max, 15, 600)

            # Camera Selector
            cameras = [self.reflection_camera, self.free_camera, self.orbit_camera]
            current_camera = cameras.index(self.camera)
            camera_changed, selected_index = imgui.combo(
                "Camera Mode",
                current_camera,
                [cam.__class__.__name__ for cam in cameras],
            )

            if camera_changed:
                self.camera = cameras[selected_index]

            # Wireframe Toggle
            _, self.wireframe = imgui.checkbox("Wireframe", self.wireframe)
            if self.wireframe:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            else:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

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

            imgui.separator()
            if imgui.tree_node("Light"):
                self.light.debug_menu()
                imgui.tree_pop()

            imgui.separator()
            if imgui.button("Quit"):
                self.running = False


if __name__ == "__main__":
    # with cProfile.Profile() as pr:

    # initialises the scene object
    # scene = Scene(shaders='gouraud')
    scene = MainScene()

    # starts drawing the scene
    scene.start()

    # stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME)
    # stats.dump_stats(filename="last_run.prof")
