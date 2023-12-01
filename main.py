import cProfile
import pstats

import imgui
import time
import numpy as np
import pygame
import quaternion
from geomdl import BSpline, exchange, knotvector
from OpenGL import GL as gl

from camera import Camera, FreeCamera, OrbitCamera
from environment_mapping import EnvironmentMappingTexture
from model import Model
from scene import Scene
from shaders import EnvironmentShader, NewShader
from shadow_mapping import ShadowMap
from skybox import SkyBox

# from spline import get_curves


class MainScene(Scene):
    def __init__(self):
        Scene.__init__(self)
        self.light.position = (-0.2, -1.0, -0.3)

        # cube = Model()

        self.reflection_camera = Camera(position=(35, 5, -45))
        self.environment = EnvironmentMappingTexture(
            self.reflection_camera, width=400, height=400
        )

        self.skybox = SkyBox()
        self.shadows = ShadowMap(light=self.light)
        self.cube = Model.from_obj("colour_cube.obj")

        self.london = Model.from_obj("london.obj", shader=NewShader())
        Model.from_obj("shard.obj", shader=EnvironmentShader())
        Model.from_obj(
            "colour_cube.obj", position=(35, 5, -45), shader=EnvironmentShader()
        )

        # self.m = 0
        # self.h = 0

        face1_center = [-16.6, 5.52, 4.38]
        face2_center = [-18.3, 5.52, 2.66]
        face3_center = [-20.1, 5.52, 4.38]
        self.face1_hour = Model.from_obj(
            "hour_hand.obj", name="face1_hour", position=face1_center
        )
        self.face1_minute = Model.from_obj(
            "minute_hand.obj", name="face1_minute", position=face1_center
        )
        self.face2_hour = Model.from_obj(
            "hour_hand.obj", name="face2_hour", position=face2_center
        )
        self.face2_minute = Model.from_obj(
            "minute_hand.obj", name="face2_minute", position=face2_center
        )
        self.face3_hour = Model.from_obj(
            "hour_hand.obj", name="face3_hour", position=face3_center
        )
        self.face3_minute = Model.from_obj(
            "minute_hand.obj", name="face3_minute", position=face3_center
        )

        self.dino = Model.from_obj(
            "dino_body.obj",
            rotation=quaternion.from_rotation_vector((0, np.pi, 0)),
            scale=0.08,
        )
        self.dino_left_wing = Model.from_obj(
            "dino_left.obj", position=(2.5, 0, 2), parent=self.dino
        )
        self.dino_right_wing = Model.from_obj(
            "dino_right.obj", position=(-2.5, 0, 2), parent=self.dino
        )

        self.dino_path = BSpline.Curve()
        self.dino_path.degree = 3
        self.dino_path.ctrlpts = exchange.import_txt("./dino_path.txt")
        self.dino_path.knotvector = knotvector.generate(
            self.dino_path.degree, self.dino_path.ctrlpts_size
        )

        self.orbit_camera = OrbitCamera(
            parent=self.dino,
            rotation=quaternion.from_rotation_vector((0, np.pi, 0)),
        )
        self.free_camera = FreeCamera()
        self.camera = self.orbit_camera

        with open("./credits.txt", encoding="utf-8") as credits_list:
            self.credits = credits_list.read()

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

        t = (pygame.time.get_ticks() / 30000) % 1
        path_derivatives = self.dino_path.derivatives(t, order=1)
        self.dino.position = path_derivatives[
            0
        ]  # 0th derivative at t, i.e. the original function at t

        forward = path_derivatives[1] / np.linalg.norm(
            path_derivatives[1]
        )  # Path normal, aka forward vector on the path
        right = np.cross([0, 1, 0], forward)
        right = right / np.linalg.norm(right)
        up = np.cross(forward, right)
        up = up / np.linalg.norm(up)

        rotation = np.identity(3)
        rotation[:, 0] = right
        rotation[:, 1] = up
        rotation[:, 2] = forward

        self.dino.rotation = quaternion.from_rotation_matrix(rotation)

        t = time.localtime()
        minute_decimal = t.tm_min / 60
        hour_decimal = ((t.tm_hour % 12) / 12) + (minute_decimal / 10)
        # minute_decimal = self.m / 60
        # hour_decimal = ((self.h % 12) / 12) + (self.h / 10)

        minute_rotation = quaternion.from_rotation_vector(
            [-minute_decimal * 2 * np.pi, 0, 0]
        )
        hour_rotation = quaternion.from_rotation_vector(
            [-hour_decimal * 2 * np.pi, 0, 0]
        )

        face2_direction = quaternion.from_rotation_vector([0, np.pi / 2, 0])
        face3_direction = quaternion.from_rotation_vector([0, np.pi, 0])

        self.face1_hour.rotation = hour_rotation
        self.face1_minute.rotation = minute_rotation
        self.face2_hour.rotation = face2_direction * hour_rotation
        self.face2_minute.rotation = face2_direction * minute_rotation
        self.face3_hour.rotation = face3_direction * hour_rotation
        self.face3_minute.rotation = face3_direction * minute_rotation

        # self.face1_hour.rotation = quaternion.from_rotation_vector([])

        # tick = (pygame.time.get_ticks()/10000) % 14

        # if int(tick) > len(self.dino_path) - 1:
        #     print(f"ERROR: TRYING TO ACCESS INDEX {int(tick)} for {tick}")
        #     tick = len(self.dino_path) - 1

        # self.dino_pos = self.dino_path[int(tick)].evaluate(float(tick % 1))[:,0]
        # self.dino.position = self.dino_pos.tolist()

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
            imgui.text(
                f"FPS: {self.clock.get_fps():.2f} ({self.clock.get_time():.2f}ms)"
            )

            if imgui.tree_node("Settings"):
                _, self.fps_max = imgui.slider_float("Max FPS", self.fps_max, 15, 600)

                _, self.x_sensitivity = imgui.slider_float(
                    "Horizontal mouse sensitivity", self.x_sensitivity, -10, 10
                )
                _, self.y_sensitivity = imgui.slider_float(
                    "Vertical mouse sensitivity", self.y_sensitivity, -10, 10
                )

                near_clip_changed, self.near_clipping = imgui.slider_float(
                    "Near clipping plane", self.near_clipping, 0.01, 20
                )
                far_clip_changed, self.far_clipping = imgui.slider_float(
                    "Far clipping plane", self.far_clipping, 25, 2500
                )
                fov_changed, self.fov = imgui.slider_float("FOV", self.fov, 30, 150)

                if near_clip_changed or far_clip_changed or fov_changed:
                    self.update_viewport()

                imgui.tree_pop()

            imgui.separator()
            if imgui.tree_node("Debug"):
                # _, self.h = imgui.slider_float("Hour sim", self.h, 0, 23)
                # _, self.m = imgui.slider_float("Min sim", self.m, 0, 60)
                imgui.text(
                    f"OpenGL v{gl.glGetIntegerv(gl.GL_MAJOR_VERSION)}.{gl.glGetIntegerv(gl.GL_MINOR_VERSION)}"
                )
                imgui.plot_lines(
                    "Frametime",
                    np.array(self.frame_times, dtype=np.float32),
                    scale_min=0.0,
                )

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
                imgui.tree_pop()

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
            if imgui.tree_node("Credits"):
                with imgui.begin_child("credits_scroll", 0.0, 200.0):
                    imgui.text_wrapped(self.credits)
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
