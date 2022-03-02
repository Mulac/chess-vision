import pyrealsense2 as rs
import numpy as np
import argparse
import pickle
import cv2


class Camera:
    def __init__(self, pipeline=None, depth=False):
        self.cancel_signal = True
        self.depth = depth
        if pipeline is None:
            pipeline = self.setup_pipeline()
        self.pipeline = pipeline

    def setup_pipeline(cls):
        # Configure depth and color streams
        pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()

        if not any(s.get_info(rs.camera_info.name) == 'RGB Camera' for s in device.sensors):
            raise EnvironmentError("The demo requires Depth camera with Color sensor")

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

        pipeline.start(config)
        # sensor = pipeline.get_active_profile().get_device().query_sensors()[1]
        # sensor.set_option(rs.option.exposure, 200000) # Set the exposure anytime during the operation
        device.hardware_reset()

        return pipeline

    def to_numpy(cls, frame):
        return np.asanyarray(frame.get_data()).copy()

    def loop(self, callback):
        while True:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if self.depth:
                depth_frame = frames.get_depth_frame()
            
            if not color_frame or (not depth_frame and self.depth):
                print(f"ERROR: failed to fetch frames")
                continue

            if self.depth:
                cancel = callback(self.to_numpy(color_frame), self.to_numpy(depth_frame))
            else:
                cancel = callback(self.to_numpy(color_frame))

            if cancel:
                return

    def close(self):
        self.pipeline.stop()


def main(args):
    picklefile = f'{args.dir}/{args.game_name}.pkl'
    camera = Camera(depth=True)

    def record(color, depth):
        cv2.imwrite("data/current.jpg", color.copy())
        pickle.dump({"color": color.copy(), "depth": depth.copy()}, pkl_file)
        
    try:
        pkl_file = open(picklefile, "wb")
        camera.loop(record)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nsaving pickle file...")
        camera.close()
        pkl_file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Will record a recorded chess game, saving it to disk. \
                        [ENTER] will take a screenshot.')
    parser.add_argument('game_name', type=str,
                        help='the name of the game to replay')
    parser.add_argument('--dir', type=str, metavar='directory', default='games',
                        help='the directory the game file can be found in')

    main(parser.parse_args())