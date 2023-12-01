"""Run the Guraffic Park scene with a debugger attached.
"""

import cProfile
import pstats

from main_scene import MainScene

if __name__ == "__main__":
    # Profile the code with cProfile
    with cProfile.Profile() as pr:
        scene = MainScene()
        scene.start()

    # Save the profile to `last_run.prof`
    # This can be view with `snakeviz last_run.prof`
    # Snakeviz will have to be installed first with `pip install snakeviz`
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename="last_run.prof")
