
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_blender.geometry import BlenderMesh
# from compas_blender.helpers import mesh_from_bmesh
from compas_blender.utilities import clear_layer
from compas_blender.utilities import draw_cylinder
from compas_blender.utilities import draw_plane
from compas_blender.utilities import draw_line
from compas_blender.utilities import get_objects
from compas_blender.utilities import get_points
from compas_blender.utilities import set_select
from compas_blender.utilities import set_deselect
# from compas_blender.utilities import get_object_location
from compas_blender.utilities import set_objects_coordinates
from compas_blender.utilities import get_object_property
from compas_blender.utilities import set_object_property
# from compas_blender.utilities import xdraw_mesh
from compas_blender.utilities import draw_text

from compas.geometry import cross_vectors
from compas.geometry import subtract_vectors

from compas_fea.utilities import colorbar
# from compas_fea.utilities import extrude_mesh
# from compas_fea.utilities import network_order
from compas_fea.utilities import postprocess
# from compas_fea.utilities import tets_from_vertices_faces
# from compas_fea.utilities import plotvoxels

from numpy import array
from numpy import hstack
from numpy import max
from numpy import newaxis
from numpy import where
from numpy.linalg import norm

try:
    import bpy
except ImportError:
    pass

# import json


__author__    = ['Andrew Liew <liew@arch.ethz.ch>']
__copyright__ = 'Copyright 2018, BLOCK Research Group - ETH Zurich'
__license__   = 'MIT License'
__email__     = 'liew@arch.ethz.ch'


__all__ = [
    'add_nodes_elements_from_bmesh',
    'add_nodes_elements_from_layers',
#     'add_tets_from_bmesh',
#     'add_nset_from_bmeshes',
#     'add_elset_from_bmeshes',
#     'add_nset_from_objects',
    'plot_data',
#     'plot_voxels',
#     'mesh_extrude',
    'plot_reaction_forces',
    'plot_concentrated_forces',
]


def add_nodes_elements_from_bmesh(structure, bmesh, line_type=None, mesh_type=None, thermal=False):

    """ Adds the Blender mesh's nodes, edges and faces to the Structure object.

    Parameters
    ----------
    structure : obj
        Structure object to update.
    bmesh : obj
        Blender mesh object.
    line_type : str
        Element type for lines (bmesh edges).
    mesh_type : str
        Element type for meshes.
    thermal : bool
        Thermal properties on or off.

    Returns
    -------
    list
        Node keys that were added to the Structure.
    list
        Element keys that were added to the Structure.

    """

    blendermesh = BlenderMesh(bmesh)
    vertices = blendermesh.get_vertices_coordinates()
    edges    = blendermesh.get_edges_vertex_indices()
    faces    = blendermesh.get_faces_vertex_indices()

    added_nodes    = set()
    added_elements = set()

    for xyz in vertices.values():
        node = structure.add_node(xyz=xyz)
        added_nodes.add(node)

    if line_type and edges:

        ex   = get_object_property(object=bmesh, property='ex')
        ey   = get_object_property(object=bmesh, property='ey')
        axes = {'ex': list(ex) if ex else ex, 'ey': list(ey) if ey else ey}

        for u, v in edges.values():

            sp_xyz = vertices[u]
            ep_xyz = vertices[v]
            sp = structure.check_node_exists(sp_xyz)
            ep = structure.check_node_exists(ep_xyz)
            ez = subtract_vectors(ep_xyz, sp_xyz)
            if ex and not ey:
                ey = cross_vectors(ex, ez)
            axes['ey'] = ey
            axes['ez'] = ez
            ekey = structure.add_element(nodes=[sp, ep], type=line_type, thermal=thermal, axes=axes)
            if ekey is not None:
                added_elements.add(ekey)

#     if mesh_type:

#         if mesh_type in ['HexahedronElement', 'TetrahedronElement', 'SolidElement', 'PentahedronElement']:
#             nodes = [structure.check_node_exists(i) for i in vertices]
#             e = structure.add_element(nodes=nodes, type=mesh_type, acoustic=acoustic, thermal=thermal)
#             if e is not None:
#                 created_elements.add(e)

#         else:
#             try:
#                 dic = json.loads(name.replace("'", '"'))
#                 ex = dic.get('ex', None)
#                 ey = dic.get('ey', None)
#                 if ex and ey:
#                     ez = cross_vectors(ex, ey)
#                 else:
#                     ez = None
#             except:
#                 ex = None
#                 ey = None
#                 ez = None
#             axes = {'ex': ex, 'ey': ey, 'ez': ez}

#             for face in faces:
#                 nodes = [structure.check_node_exists(vertices[i]) for i in face]
#                 e = structure.add_element(nodes=nodes, type=mesh_type, acoustic=acoustic, thermal=thermal, axes=axes)
#                 if e is not None:
#                     created_elements.add(e)

    return list(added_nodes), list(added_elements)


def add_nodes_elements_from_layers(structure, layers, line_type=None, mesh_type=None, thermal=False, pA=None, pL=None):

    """ Adds node and element data from Blender layers to Structure object.

    Parameters
    ----------
    structure : obj
        Structure object to update.
    layers : list
        Layer string names to extract nodes and elements.
    line_type : str
        Element type for lines (bmesh edges).
    mesh_type : str
        Element type for meshes.
    thermal : bool
        Thermal properties on or off.
    pA : float
        Mass area density [kg/m2].
    pL : float
        Mass length density [kg/m].

    Returns
    -------
    list
        Node keys that were added to the Structure.
    list
        Element keys that were added to the Structure.

    """

    if isinstance(layers, str):
        layers = [layers]

    added_nodes    = set()
    added_elements = set()

    for layer in layers:

        elset = set()

        for bmesh in get_objects(layer=layer):

            nodes, elements = add_nodes_elements_from_bmesh(structure=structure, bmesh=bmesh, line_type=line_type,
                                                            mesh_type=mesh_type, thermal=thermal)
            added_nodes.update(nodes)
            added_elements.update(elements)
            elset.update(elements)

        structure.add_set(name=layer, type='element', selection=list(elset))

    return list(added_nodes), list(added_elements)


# def add_tets_from_bmesh(structure, name, bmesh, draw_tets=False, volume=None, layer=19, acoustic=False, thermal=False):

#     """ Adds tetrahedron elements from a Blender mesh to the Structure object.

#     Parameters
#     ----------
#     structure : obj
#         Structure object to update.
#     name : str
#         Name for the element set of tetrahedrons.
#     bmesh : obj
#         The Blender mesh representing the outer surface.
#     draw_tets : bool
#         Draw the generated tetrahedrons.
#     volume : float
#         Maximum volume for tets.
#     layer : int
#         Layer to draw tetrahedrons if draw_tets=True.
#     acoustic : bool
#         Acoustic properties on or off.
#     thermal : bool
#         Thermal properties on or off.

#     Returns
#     -------
#     None

#     """

#     blendermesh = BlenderMesh(bmesh)
#     vertices = blendermesh.get_vertex_coordinates()
#     faces = blendermesh.get_face_vertex_indices()

#     tets_points, tets_elements = tets_from_vertices_faces(vertices=vertices, faces=faces, volume=volume)

#     for point in tets_points:
#         structure.add_node(point)

#     ekeys = []
#     for element in tets_elements:
#         nodes = [structure.check_node_exists(tets_points[i]) for i in element]
#         ekey = structure.add_element(nodes=nodes, type='TetrahedronElement', acoustic=acoustic, thermal=thermal)
#         ekeys.append(ekey)
#     structure.add_set(name=name, type='element', selection=ekeys)

#     if draw_tets:
#         tet_faces = [[0, 1, 2], [1, 3, 2], [1, 3, 0], [0, 2, 3]]
#         for i, points in enumerate(tets_elements):
#             xyz = [tets_points[j] for j in points]
#             xdraw_mesh(name=str(i), vertices=xyz, faces=tet_faces, layer=layer)


# def add_elset_from_bmeshes(structure, name, bmeshes=None, layer=None):

#     """ Adds the Blender meshes' edges and faces as an element set.

#     Parameters
#     ----------
#     structure : obj
#         Structure object to update.
#     name : str
#         Name of the new element set.
#     bmeshes : list
#         Blender mesh objects to extract edges and faces.
#     layer : int
#         Layer to get bmeshes from if bmeshes are not given.

#     Returns
#     -------
#     None

#     Notes
#     -----
#     - Either bmeshes or layer should be given, not both.

#     """

#     if layer is not None:
#         bmeshes = [object for object in get_objects(layer=layer) if object.type == 'MESH']

#     elements = []

#     for bmesh in bmeshes:

#         blendermesh = BlenderMesh(bmesh)
#         vertices = blendermesh.get_vertex_coordinates()
#         edges    = blendermesh.get_edge_vertex_indices()
#         faces    = blendermesh.get_face_vertex_indices()

#         for u, v in edges:
#             sp = structure.check_node_exists(vertices[u])
#             ep = structure.check_node_exists(vertices[v])
#             element = structure.check_element_exists([sp, ep])
#             if element is not None:
#                 elements.append(element)

#         for face in faces:
#             nodes = [structure.check_node_exists(vertices[i]) for i in face]
#             element = structure.check_element_exists(nodes)
#             if element is not None:
#                 elements.append(element)

#     structure.add_set(name=name, type='element', selection=elements)


# def add_nset_from_bmeshes(structure, name, bmeshes=None, layer=None):

#     """ Adds the Blender meshes' vertices as a node set.

#     Parameters
#     ----------
#     structure : obj
#         Structure object to update.
#     name : str
#         Name of the new node set.
#     bmeshes : list
#         Blender mesh objects to extract vertices.
#     layer : int
#         Layer to get bmeshes from if bmeshes are not given.

#     Returns
#     -------
#     None

#     Notes
#     -----
#     - Either bmeshes or layer should be given, not both.

#     """

#     if layer is not None:
#         bmeshes = [object for object in get_objects(layer=layer) if object.type == 'MESH']

#     nodes = []
#     for bmesh in bmeshes:
#         for vertex in BlenderMesh(bmesh).get_vertex_coordinates():
#             node = structure.check_node_exists(vertex)
#             if node is not None:
#                 nodes.append(node)
#     structure.add_set(name=name, type='node', selection=nodes)


def add_nsets_from_layers(structure, layers):

    """ Adds node sets from objects in layers.

    Parameters
    ----------
    structure : obj
        Structure object to update.
    layers : list
        Layers to get objects from.

    Returns
    -------
    None

    """

    if isinstance(layers, str):
        layers = [layers]

    for layer in layers:

        nodes = []

        for point in get_points(layer=layer):
            nodes.append(structure.check_node_exists(list(point.location)))

        # ADD MESHES HERE AND ADD VERTICES TO NODES
        # for object in get_objects(layer=layer):

        structure.add_set(name=layer, type='node', selection=nodes)


# def mesh_extrude(structure, bmesh, layers, thickness, mesh_name='', links_name='', blocks_name=''):

#     """ Extrudes a Blender mesh and adds/creates elements.

#     Parameters
#     ----------
#     structure : obj
#         Structure object to update.
#     bmesh : obj
#         Blender mesh object.
#     layers : int
#         Number of layers.
#     thickness : float
#         Layer thickness.
#     blocks_name : str
#         Name of set for solid elements.
#     mesh_name : str
#         Name of set for mesh on final surface.
#     links_name : str
#         Name of set for adding links along extrusion.

#     Returns
#     -------
#     None

#     Notes
#     -----
#     - Extrusion is along the vertex normals.

#     """

#     mesh = mesh_from_bmesh(bmesh)
#     extrude_mesh(structure=structure, mesh=mesh, layers=layers, thickness=thickness, mesh_name=mesh_name,
#                  links_name=links_name, blocks_name=blocks_name)


def plot_data(structure, step, field='um', layer=None, scale=1.0, radius=0.05, cbar=[None, None], iptype='mean',
              nodal='mean', mode='', cbar_size=1):

    """ Plots analysis results on the deformed shape of the Structure.

    Parameters
    ----------
    structure : obj
        Structure object.
    step : str
        Name of the Step.
    field : str
        Field to plot, e.g. 'um', 'sxx', 'sm1'.
    layer : str
        Layer name for plotting.
    scale : float
        Scale on displacements for the deformed plot.
    radius : float
        Radius of the pipe visualisation meshes.
    cbar : list
        Minimum and maximum limits on the colorbar.
    iptype : str
        'mean', 'max' or 'min' of an element's integration point data.
    nodal : str
        'mean', 'max' or 'min' for nodal values.
    mode : int
        Mode or frequency number to plot, for modal, harmonic or buckling analysis.
    cbar_size : float
        Scale on the size of the colorbar.

    Returns
    -------
    None

    Notes
    -----
    - Pipe visualisation of line elements is not based on the element section.

    """

    if field in ['smaxp', 'smises']:
        nodal  = 'max'
        iptype = 'max'

    elif field in ['sminp']:
        nodal  = 'min'
        iptype = 'min'

    # Create and clear Blender layer

    if not layer:
        layer = '{0}-{1}{2}'.format(step, field, mode)

    clear_layer(layer=layer)

    # Node and element data

    nodes      = structure.nodes_xyz()
    elements   = [structure.elements[i].nodes for i in sorted(structure.elements, key=int)]
    nodal_data = structure.results[step]['nodal']
    nkeys      = sorted(structure.nodes, key=int)

    ux = [nodal_data['ux{0}'.format(mode)][i] for i in nkeys]
    uy = [nodal_data['uy{0}'.format(mode)][i] for i in nkeys]
    uz = [nodal_data['uz{0}'.format(mode)][i] for i in nkeys]

    try:
        data  = [nodal_data['{0}{1}'.format(field, mode)][i] for i in nkeys]
        dtype = 'nodal'

    except(Exception):
        data  = structure.results[step]['element'][field]
        dtype = 'element'

    # Postprocess

    result = postprocess(nodes, elements, ux, uy, uz, data, dtype, scale, cbar, 1, iptype, nodal)

    try:
        toc, U, cnodes, fabs, fscaled, celements, eabs = result
        U = array(U)
        print('\n***** Data processed : {0} s *****'.format(toc))

    except:
        print('\n***** Error encountered during data processing or plotting *****')

    # Plot meshes

    npts = 8
    mesh_faces = []
    pipes      = []

    for element, nodes in enumerate(elements):

        n = len(nodes)

        if n == 2:

            u, v = nodes
            pipe = draw_cylinder(start=U[u], end=U[v], radius=radius, div=npts, layer=layer)
            pipes.append(pipe)

            if dtype == 'element':
                col1 = col2 = celements[element]

            elif dtype == 'nodal':
                col1 = cnodes[u]
                col2 = cnodes[v]

            blendermesh = BlenderMesh(object=pipe)
            blendermesh.set_vertices_colors({i: col1 for i in range(0, 2*npts, 2)})
            blendermesh.set_vertices_colors({i: col2 for i in range(1, 2*npts, 2)})

        elif n in [3, 4]:

            mesh_faces.append(nodes)

#     if mesh_faces:
#         bmesh = xdraw_mesh(name='bmesh', vertices=U, faces=mesh_faces, layer=layer)
#         blendermesh = BlenderMesh(bmesh)
#         blendermesh.set_vertex_colors(vertices=range(U.shape[0]), colors=cnodes)

    # Plot colourbar

    xr, yr, _ = structure.node_bounds()
    yran = yr[1] - yr[0] if yr[1] - yr[0] else 1
    s    = yran * 0.1 * cbar_size
    xmin = xr[1] + 3 * s
    ymin = yr[0]

    cmesh = draw_plane(name='colorbar', Lx=s, dx=s, Ly=10*s, dy=s, layer=layer)
    set_objects_coordinates(objects=[cmesh], coords=[[xmin, ymin, 0]])
    blendermesh = BlenderMesh(object=cmesh)
    vertices    = blendermesh.get_vertices_coordinates().values()

    y  = array(list(vertices))[:, 1]
    yn = yran * cbar_size
    colors = colorbar(((y - ymin - 0.5 * yn) * 2 / yn)[:, newaxis], input='array', type=1)
    blendermesh.set_vertices_colors({i: j for i, j in zip(range(len(vertices)), colors)})

    set_deselect()
    set_select(objects=pipes + [cmesh])
    bpy.ops.object.join()

    h = 0.6 * s

    for i in range(5):

        x0 = xmin + 1.2 * s
        yu = ymin + (5.8 + i) * s
        yl = ymin + (3.8 - i) * s
        vu = +max([eabs, fabs]) * (i + 1) / 5.
        vl = -max([eabs, fabs]) * (i + 1) / 5.

        draw_text(radius=h, pos=[x0, yu, 0], text='{0:.3g}'.format(vu), layer=layer)
        draw_text(radius=h, pos=[x0, yl, 0], text='{0:.3g}'.format(vl), layer=layer)

    draw_text(radius=h, pos=[x0,  ymin + 4.8 * s, 0], text='0', layer=layer)
    draw_text(radius=h, pos=[xmin, ymin + 12 * s, 0], text='Step:{0}   Field:{1}'.format(step, field), layer=layer)


def plot_reaction_forces(structure, step, layer=None, scale=1.0):

    """ Plots reaction forces for the Structure analysis results.

    Parameters
    ----------
    structure : obj
        Structure object.
    step : str
        Name of the Step.
    layer : str
        Layer name for plotting.
    scale : float
        Scale of the arrows.

    Returns
    -------
    None

    """

    if not layer:
        layer = '{0}-{1}'.format(step, 'reactions')

    clear_layer(layer=layer)

    rfx   = array(list(structure.results[step]['nodal']['rfx'].values()))[:, newaxis]
    rfy   = array(list(structure.results[step]['nodal']['rfy'].values()))[:, newaxis]
    rfz   = array(list(structure.results[step]['nodal']['rfz'].values()))[:, newaxis]
    rf    = hstack([rfx, rfy, rfz])
    rfm   = norm(rf, axis=1)
    rmax  = max(rfm)
    nodes = array(structure.nodes_xyz())

    for i in where(rfm > 0)[0]:

        sp   = nodes[i, :]
        ep   = nodes[i, :] + rf[i, :] * -scale * 0.001
        col  = colorbar(rfm[i] / rmax, input='float', type=1)
        line = draw_line(start=sp, end=ep, width=0.01, color=col)

        set_object_property(object=line, property='rfx', value=rf[i, 0])
        set_object_property(object=line, property='rfy', value=rf[i, 1])
        set_object_property(object=line, property='rfz', value=rf[i, 2])
        set_object_property(object=line, property='rfm', value=rfm[i])


def plot_concentrated_forces(structure, step, layer=None, scale=1.0):

    """ Plots reaction forces for the Structure analysis results.

    Parameters
    ----------
    structure : obj
        Structure object.
    step : str
        Name of the Step.
    layer : str
        Layer name for plotting.
    scale : float
        Scale of the arrows.

    Returns
    -------
    None

    """

    if not layer:
        layer = '{0}-{1}'.format(step, 'forces')

    clear_layer(layer=layer)

    cfx   = array(list(structure.results[step]['nodal']['cfx'].values()))[:, newaxis]
    cfy   = array(list(structure.results[step]['nodal']['cfy'].values()))[:, newaxis]
    cfz   = array(list(structure.results[step]['nodal']['cfz'].values()))[:, newaxis]
    cf    = hstack([cfx, cfy, cfz])
    cfm   = norm(cf, axis=1)
    cmax  = max(cfm)
    nodes = array(structure.nodes_xyz())

    for i in where(cfm > 0)[0]:

        sp   = nodes[i, :]
        ep   = nodes[i, :] + cf[i, :] * -scale * 0.001
        col  = colorbar(cfm[i] / cmax, input='float', type=1)
        line = draw_line(start=sp, end=ep, width=0.01, color=col)

        set_object_property(object=line, property='cfx', value=cf[i, 0])
        set_object_property(object=line, property='cfy', value=cf[i, 1])
        set_object_property(object=line, property='cfz', value=cf[i, 2])
        set_object_property(object=line, property='cfm', value=cfm[i])


# def plot_voxels(structure, step, field='smises', cbar=[None, None], iptype='mean', nodal='mean',
#                 vdx=None, mode='', plot='vtk'):

#     """ Voxel 4D visualisation.

#     Parameters
#     ----------
#     structure : obj
#         Structure object.
#     step : str
#         Name of the Step.
#     field : str
#         Field to plot, e.g. 'smises'.
#     cbar : list
#         Minimum and maximum limits on the colorbar.
#     iptype : str
#         'mean', 'max' or 'min' of an element's integration point data.
#     nodal : str
#         'mean', 'max' or 'min' for nodal values.
#     vdx : float
#         Voxel spacing.
#     mode : int
#         mode or frequency number to plot, in case of modal, harmonic or buckling analysis.
#     plot : str
#         Plot voxels with 'vtk'.

#     Returns
#     -------
#     None

#     """

#     # Node and element data

#     nodes = structure.nodes_xyz()
#     elements = [structure.elements[i].nodes for i in sorted(structure.elements, key=int)]
#     nodal_data = structure.results[step]['nodal']
#     nkeys = sorted(structure.nodes, key=int)
#     ux = [nodal_data['ux{0}'.format(mode)][i] for i in nkeys]
#     uy = [nodal_data['uy{0}'.format(mode)][i] for i in nkeys]
#     uz = [nodal_data['uz{0}'.format(mode)][i] for i in nkeys]

#     try:
#         data = [nodal_data['{0}{1}'.format(field, mode)][i] for i in nkeys]
#         dtype = 'nodal'
#     except(Exception):
#         data = structure.results[step]['element'][field]
#         dtype = 'element'

#     # Postprocess

#     result = postprocess(nodes, elements, ux, uy, uz, data, dtype, 1, cbar, 1, iptype, nodal)

#     try:
#         toc, U, cnodes, fabs, fscaled, celements, eabs = result
#         U = array(U)
#         print('\n***** Data processed : {0:.3f} s *****'.format(toc))
#     except:
#         print('\n***** Error encountered during data processing or plotting *****')

#     plotvoxels(values=fscaled, U=U, vdx=vdx, plot=plot)


# ==============================================================================
# Debugging
# ==============================================================================

if __name__ == "__main__":

    pass
