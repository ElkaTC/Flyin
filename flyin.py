from visualizer import Renderer
import sys
   

if __name__ == "__main__":
	chosen_map = None

	if len(sys.argv) > 2:
		print("[ERROR] -> Usage: python flyin.py <file.txt>")
		sys.exit(1)

	if len(sys.argv) == 2:
		if not sys.argv[1].endswith(".txt"):
			print("[ERROR] -> Usage: python flyin.py <file.txt>")
			sys.exit(1)
		chosen_map = sys.argv[1]

	app = Renderer(default_map=chosen_map)
	app.run()