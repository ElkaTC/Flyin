from visualizer import Renderer
import sys


if __name__ == "__main__":
    try:
        chosen_map = None
        flag = None
        args = sys.argv[1:]

        if len(args) > 2:
            print(
                "[ERROR] -> Usage: python flyin.py <file.txt> [debug]"
                )
            sys.exit(1)

        for arg in args:
            if arg == "debug":
                flag = "debug"
            elif arg.endswith(".txt"):
                chosen_map = arg
            else:
                print(f"[ERROR] -> Argument unkown: '{arg}'")
                print("[ERROR] -> Usage: python flyin.py <file.txt> [debug]")
                sys.exit(1)

        app = Renderer(default_map=chosen_map)
        app.simulator.flag = flag
        app.run()

    except KeyboardInterrupt:
        sys.exit(1)
