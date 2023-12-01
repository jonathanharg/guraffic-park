from geomdl import exchange
from geomdl import BSpline
from geomdl import knotvector

data = exchange.import_txt("./dino_path.txt")

curve = BSpline.Curve()

test = BSpline.Curve()
test.degree = 3
test.ctrlpts = [[0,0,-1],[1,1,0],[0,0,1],[-1,1,0],[0,0,-1]]
test.knotvector = knotvector.generate(test.degree, test.ctrlpts_size)

# exchange.export_txt(test, "./demo.txt")

print(data)
print(type(data))