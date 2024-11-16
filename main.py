import easygui
import os
import re
import platformdirs
import json

_cache_dir = platformdirs.user_cache_dir(
    appname="obj-exporter",
    appauthor="francescozoccheddu",
    version="0.1",
    ensure_exists=True,
)
_memo_filepath = os.path.join(_cache_dir, "memo.json")
_memo = None


def _init_memo() -> None:
    global _memo
    if _memo is None:
        if os.path.isfile(_memo_filepath):
            with open(_memo_filepath, "r") as file:
                _memo = json.load(file)
        else:
            _memo = {}


def _memorize(key: str, value: str) -> None:
    _init_memo()
    global _memo
    _memo[key] = value
    with open(_memo_filepath, "w") as file:
        json.dump(_memo, file)


def _recall(key: str, default: str | None = None) -> str | None:
    global _memo
    _init_memo()
    return _memo.get(key, default)


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
    def float_tuple(self) -> tuple[float, float, float]:
        return self._x, self._y, self._z

    def __hash__(self) -> int:
        return hash(self.float_tuple)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Vec) and self.float_tuple == value.float_tuple


class Vertex:

    def __init__(self, pos: Vec, norm: Vec) -> None:
        self._pos = pos
        self._norm = norm

    @property
    def pos(self):
        return self._pos

    @property
    def norm(self):
        return self._norm

    @property
    def float_tuple(self) -> tuple[float, float, float]:
        return *self._pos.float_tuple, *self._norm.float_tuple

    def __hash__(self) -> int:
        return hash(self.float_tuple)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Vertex) and self.float_tuple == value.float_tuple


class Mesh:

    def __init__(self, vertices: list[Vertex], indices: list[int]) -> None:
        self._vertices = vertices
        self._indices = indices

    @property
    def vertices(self) -> list[Vertex]:
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
            map(str, map(lambda v: sep.join(map(str, v.float_tuple)), self.vertices))
        )
        mesh += sep
        return mesh

    def to_cpp_str(self) -> str:
        raise NotImplementedError()


def read_obj_file(filepath: str) -> dict[str, Mesh]:
    with open(filepath, "r") as file:
        lines = file.readlines()
    command_re = re.compile("(?P<cmd>v|vn|f|o) (?P<data>.*)")
    vec_re = re.compile("(?P<x>[^\\s]+) (?P<y>[^\\s]+) (?P<z>[^\\s]+)")
    ind_re = re.compile(
        "(?P<p0>\\d+)//(?P<n0>\\d+) (?P<p1>\\d+)//(?P<n1>\\d+) (?P<p2>\\d+)//(?P<n2>\\d+)"
    )
    meshes = {}
    mesh = None
    positions = []
    normals = []
    for line in lines:
        matches = command_re.search(line)
        if matches is not None:
            cmd = matches["cmd"]
            data = matches["data"]
            if cmd == "o":
                meshes[data] = mesh = {
                    "position_indices": [],
                    "normal_indices": [],
                }
            elif cmd == "f":
                ind = ind_re.search(data).groupdict()
                mesh["position_indices"].extend(
                    [int(ind[k]) - 1 for k in ["p0", "p1", "p2"]]
                )
                mesh["normal_indices"].extend(
                    [int(ind[k]) - 1 for k in ["n0", "n1", "n2"]]
                )
            elif cmd in ["v", "vn"]:
                vec = vec_re.search(data).groupdict()
                if cmd == "v":
                    buffer = positions
                else:
                    buffer = normals
                buffer.append([float(vec[k]) for k in ["x", "y", "z"]])

    def linearize_mesh(mesh: dict[str, list]) -> Mesh:
        vertices = []
        indices = []
        vertex_map = {}
        for pi_1b, ni_1b in zip(mesh["position_indices"], mesh["normal_indices"]):
            vertex = Vertex(Vec(*positions[pi_1b]), Vec(*normals[ni_1b]))
            vi = vertex_map.get(vertex)
            if vi is None:
                vi = len(vertices)
                vertex_map[vertex] = vi
                vertices.append(vertex)
            indices.append(vi)

        return Mesh(vertices, indices)

    return {name: linearize_mesh(mesh) for name, mesh in meshes.items()}


def run_gui() -> bool:
    in_filepath = easygui.fileopenbox(
        title="Import OBJ",
        msg="Choose the OBJ file to import",
        filetypes=["*.obj"],
        default=_recall("in_filepath"),
    )
    if in_filepath is None:
        return False
    _memorize("in_filepath", in_filepath)
    meshes = read_obj_file(in_filepath)
    out_dirpath = easygui.diropenbox(
        title="Export meshes",
        msg="Choose the directory in which to export the meshes",
        default=_recall("out_dirpath"),
    )
    if out_dirpath is None:
        return False
    _memorize("out_dirpath", out_dirpath)
    for name, mesh in meshes.items():
        basename = name
        out_filepath = os.path.join(out_dirpath, f"{basename}.mesh")
        with open(out_filepath, "w") as out_file:
            out_file.write(mesh.to_mesh_str())
    return True


if __name__ == "__main__":
    run_gui()
