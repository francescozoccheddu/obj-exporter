import stl_reader
import filedialpy


class Vec:

    def __init__(self, x: float, y: float, z: float) -> None:
        self._x = x
        self._y = y
        self._z = z

    @property
    def x(self) -> float:
        self._x

    @property
    def y(self) -> float:
        self._y

    @property
    def z(self) -> float:
        self._z

    @property
    def tuple(self) -> tuple[float, float, float]:
        return self._x, self._y, self._z


class Mesh:

    def __init__(self, vertices: list[Vec], indices: list[int]) -> None:
        self._vertices = vertices
        self._indices = indices

    @property
    def vertices(self) -> list[Vec]:
        return self._vertices

    @property
    def indices(self) -> list[int]:
        return self._indices

    def to_mesh_str(self) -> str:
        sep = "\n"
        mesh = ""
        mesh += str(len(self.indices))
        mesh += sep
        mesh += sep.join(map(str, self.indices))
        mesh += sep
        mesh += str(len(self.vertices))
        mesh += sep
        mesh += sep.join(
            map(str, map(lambda v: sep.join(map(str, v.tuple)), self.vertices))
        )
        mesh += sep
        return mesh

    def to_cpp_str(self) -> str:
        raise NotImplementedError()


def read_stl_file(filepath: str) -> Mesh:
    in_verts, in_inds = stl_reader.read(filepath)
    out_verts = [Vec(*v) for v in in_verts]
    out_inds = [i for in_tri_inds in in_inds for i in in_tri_inds]
    return Mesh(out_verts, out_inds)


def run_gui() -> bool:
    in_filepath = filedialpy.openFile(
        title="Choose the STL file to import", filter=["*.stl"]
    )
    if in_filepath == "":
        return False
    mesh = read_stl_file(in_filepath)
    out_filepath = filedialpy.saveFile(
        title="Choose the mesh file to export", filter=["*.mesh"]
    )
    if out_filepath == "":
        return False
    with open(out_filepath, "w") as out_file:
        out_file.write(mesh.to_mesh_str())
    return True


if __name__ == "__main__":
    run_gui()
