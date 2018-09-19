import os

from compas.datastructures.mesh.mesh import Mesh

from compas_fea.structure import Structure

from compas_fea.fea.ansys.writing.ansys_process import ansys_open_pre_process
from compas_fea.fea.ansys.writing.ansys_nodes_elements import write_request_mesh_areas

from compas_fea.fea.ansys.reading import get_nodes_elements_from_result_files

from compas_fea.fea.ansys import ansys_launch_process


def areas_from_mesh(structure, mesh):
    areas = {}
    fkeys = sorted(mesh.face.keys(), key=int)
    for fkey in fkeys:
        face = mesh.face_vertices(fkey)
        areas[fkey] = face
    structure.areas = areas
    return structure


def mesh_from_ansys_results(output_path, name):
    output_path = os.path.join(output_path, name + '_output')
    nodes, elements = get_nodes_elements_from_result_files(output_path)
    nkeys = sorted(nodes.keys(), key=int)
    vertices = [[nodes[k]['x'], nodes[k]['y'], nodes[k]['z']] for k in nkeys]
    fkeys = sorted(elements.keys(), key=int)
    faces = []
    for fk in fkeys:
        face = elements[fk]['nodes']
        face = face[:3]
        faces.append(face)
    mesh = Mesh.from_vertices_and_faces(vertices, faces)
    return mesh


def ansys_remesh(mesh, output_path, name, size=None):
    s = Structure(output_path, name=name)

    s.add_nodes_elements_from_mesh(mesh, 'ShellElement')
    s = areas_from_mesh(s, mesh)
    filename = name + '.txt.'
    ansys_open_pre_process(output_path, filename)
    write_request_mesh_areas(s, output_path, name, size=size, smart_size=None, div=None)
    ansys_launch_process(output_path, name, cpus=4, license='teaching', delete=True)

    mesh = mesh_from_ansys_results(output_path, name)
    return mesh


if __name__ == '__main__':

    path = '/Users/mtomas/Documents/ETH/01_research/01_vibro/02_num_exp/181100_floor_comparison/geometry/remeshing'

    name = 'remesh'
    mesh = mesh_from_ansys_results(path, name)
    print mesh
