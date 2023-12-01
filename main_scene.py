"""Guraffic Park 3D Scene. Run with `python .` or `python main_scene.py`."""

import time

import imgui
import numpy as np
import pygame
import quaternion
from geomdl import BSpline, exchange, knotvector
from OpenGL import GL as gl

from camera import Camera, FreeCamera, OrbitCamera
from environment_mapping import EnvironmentMappingTexture
from model import Model
from scene import Scene
from shaders import CartoonShader, EnvironmentShader, Shader

# from shadow_mapping import ShadowMap
from skybox import SkyBox


class MainScene(Scene):
    def __init__(self):
        Scene.__init__(self)
        self.light.position = (-0.2, -1.0, -0.3)

        self.reflection_camera = Camera(position=(35, 5, -45))
        self.environment = EnvironmentMappingTexture(
            self.reflection_camera, width=800, height=800
        )

        self.skybox = SkyBox()
        # self.shadows = ShadowMap(light=self.light)

        self.london = Model.from_obj("london.obj")
        Model.from_obj("shard.obj", shader=EnvironmentShader())

        # self.m = 0
        # self.h = 0

        #
        # Define the parts for the dinosaur
        #
        self.dino = Model.from_obj(
            "dino_body.obj",
            rotation=quaternion.from_rotation_vector((0, np.pi, 0)),
            scale=0.08,
        )
        # Parent the wings to the body & offset to the arms position
        self.dino_left_wing = Model.from_obj(
            "dino_left.obj", position=(2.5, 0, 2), parent=self.dino
        )
        self.dino_right_wing = Model.from_obj(
            "dino_right.obj", position=(-2.5, 0, 2), parent=self.dino
        )

        # Creates a piecewise polynomial to represent the dinosaurs path.
        # See lecture Week 9 Lecture 1, https://en.wikipedia.org/wiki/B-spline,
        # or https://nurbs-python.readthedocs.io/en/5.x/index.html
        self.dino_path = BSpline.Curve()
        self.dino_path.degree = 3
        self.dino_path.ctrlpts = exchange.import_txt("./dino_path.txt")
        self.dino_path.knotvector = knotvector.generate(
            self.dino_path.degree, self.dino_path.ctrlpts_size
        )

        # Create the main camera, position it, and parent it to the dinosaur
        self.orbit_camera = OrbitCamera(
            rotation=quaternion.from_rotation_vector((0, np.pi, np.pi / 6)),
            distance=4.0,
            parent=self.dino,
        )
        # Setup debug camera for the future
        self.free_camera = FreeCamera()
        # Set the active camera to the orbit camera
        self.camera = self.orbit_camera

        # Define the Big Ben clock hands
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

        # Load the credits into memory to display on the GUI
        with open("./credits.txt", encoding="utf-8") as credits_list:
            self.credits = credits_list.read()

    def run(self):
        """Run the scene each tick. No rendering is done, but any moving entities/interactions should be calculated."""

        #
        # Wing animations
        #

        # Animation parameter
        t = 500 * np.cos((np.pi / 1000) * pygame.time.get_ticks()) + 500
        # Trigonometric function to define animation of wing flaps

        wing_resting_pose = np.quaternion(1.0, 0.0, 0.0, 0.0)
        left_wing_down_pose = quaternion.from_rotation_vector((0, 0, -np.pi / 4))
        right_wing_down_pose = quaternion.from_rotation_vector((0, 0, np.pi / 4))

        flap_start = 0
        flap_end = 1000  # Take this many milliseconds to rotate

        # Spherical Linear interpolation between start and end pose
        # https://en.wikipedia.org/wiki/Slerp
        left_wing_rotation = quaternion.slerp(
            wing_resting_pose, left_wing_down_pose, flap_start, flap_end, t
        )
        right_wing_rotation = quaternion.slerp(
            wing_resting_pose, right_wing_down_pose, flap_start, flap_end, t
        )

        self.dino_left_wing.rotation = left_wing_rotation
        self.dino_right_wing.rotation = right_wing_rotation

        #
        # Dinosaur Path/Movement Animations
        #

        # Animation parameter
        t = (pygame.time.get_ticks() / 30000) % 1

        # Calculate path and its 1st derivative (normal)
        path_derivatives = self.dino_path.derivatives(t, order=1)

        # 0th derivative at t, i.e. the original function at t
        self.dino.position = path_derivatives[0]

        # Path normal, aka forward vector on the path
        forward = path_derivatives[1] / np.linalg.norm(path_derivatives[1])

        # Relative right vector
        right = np.cross([0, 1, 0], forward)
        right = right / np.linalg.norm(right)

        # Relative up vector
        up = np.cross(forward, right)
        up = up / np.linalg.norm(up)

        rotation = np.identity(3)
        rotation[:, 0] = right
        rotation[:, 1] = up
        rotation[:, 2] = forward

        self.dino.rotation = quaternion.from_rotation_matrix(rotation)

        #
        # Big Ben Clock hand animations
        #
        t = time.localtime()

        minute_decimal = t.tm_min / 60
        hour_decimal = ((t.tm_hour % 12) / 12) + (minute_decimal / 10)
        # TODO: REMOVE
        # minute_decimal = self.m / 60
        # hour_decimal = ((self.h % 12) / 12) + (self.h / 10)

        minute_rotation = quaternion.from_rotation_vector([
            -minute_decimal * 2 * np.pi, 0, 0
        ])
        hour_rotation = quaternion.from_rotation_vector([
            -hour_decimal * 2 * np.pi, 0, 0
        ])

        face2_direction = quaternion.from_rotation_vector([0, np.pi / 2, 0])
        face3_direction = quaternion.from_rotation_vector([0, np.pi, 0])

        self.face1_hour.rotation = hour_rotation
        self.face1_minute.rotation = minute_rotation

        self.face2_hour.rotation = face2_direction * hour_rotation
        self.face2_minute.rotation = face2_direction * minute_rotation

        self.face3_hour.rotation = face3_direction * hour_rotation
        self.face3_minute.rotation = face3_direction * minute_rotation

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

        for model in self.models:
            model.draw()
        gl.glUseProgram(0)
        Shader.current_shader = 0

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
        """Define the debug menu for this class. Uses the ImGui library to construct a UI. Calling this function inside an ImGui context will render this debug menu."""
        with imgui.begin("Menu", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE):
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
                # TODO: Remove
                # _, self.h = imgui.slider_float("Hour sim", self.h, 0, 23)
                # _, self.m = imgui.slider_float("Min sim", self.m, 0, 60)
                imgui.text(
                    "OpenGL"
                    f" v{gl.glGetIntegerv(gl.GL_MAJOR_VERSION)}.{gl.glGetIntegerv(gl.GL_MINOR_VERSION)}"
                )
                imgui.plot_lines(
                    "Frametime",
                    np.array(self.frame_times, dtype=np.float32),
                    scale_min=0.0,
                )

                wireframe_changed, self.wireframe = imgui.checkbox(
                    "Wireframe", self.wireframe
                )
                if wireframe_changed:
                    if self.wireframe:
                        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
                    else:
                        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
                imgui.tree_pop()

            imgui.separator()
            if imgui.tree_node("Models"):
                # Render every models debug menu
                for model in self.models:
                    if imgui.tree_node(model.name):
                        model.debug_menu()
                        imgui.tree_pop()
                imgui.tree_pop()

            imgui.separator()
            if imgui.tree_node("Camera"):
                # Render camera debug menu
                self.camera.debug_menu()
                imgui.tree_pop()

            imgui.separator()
            if imgui.tree_node("Light"):
                # Render the lights debug menu
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


# Run the scene if this file is called
if __name__ == "__main__":
    scene = MainScene()

    scene.start()
