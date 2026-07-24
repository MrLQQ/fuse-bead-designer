from fuse_bead_designer.cleanup import cleanup_cells
from fuse_bead_designer.quantize import SampledCell


def cell(color_id, distance=10.0, occupied=True):
    return SampledCell(occupied=occupied, color_id=color_id if occupied else None, distance=distance if occupied else None)


def consensus_grid(center_color="yellow", center_distance=90.0):
    return [
        [cell("black"), cell("black"), cell("black")],
        [cell("black"), cell(center_color, center_distance), cell("black")],
        [cell("black"), cell("black"), cell("black")],
    ]


def test_low_confidence_singleton_inside_consensus_is_replaced():
    cells = consensus_grid(center_color="yellow", center_distance=90.0)

    result = cleanup_cells(cells)

    assert result.cells[1][1].color_id == "black"
    assert result.changed_cells == [(1, 1)]


def test_protected_singleton_is_preserved():
    cells = consensus_grid(center_color="yellow", center_distance=90.0)

    result = cleanup_cells(cells, protected_cells={(1, 1)})

    assert result.cells[1][1].color_id == "yellow"
    assert result.changed_cells == []


def test_edges_no_consensus_and_low_confidence_boundary_are_preserved():
    edge_cells = consensus_grid(center_color="black")
    edge_cells[0][0] = cell("yellow", 90.0)
    assert cleanup_cells(edge_cells).changed_cells == []

    no_consensus = consensus_grid()
    no_consensus[0][0] = cell("red")
    no_consensus[0][1] = cell("red")
    no_consensus[0][2] = cell("red")
    assert cleanup_cells(no_consensus).changed_cells == []

    threshold = consensus_grid(center_distance=14.999)
    assert cleanup_cells(threshold).changed_cells == []
    threshold[1][1] = cell("yellow", 15.0)
    assert cleanup_cells(threshold).changed_cells == [(1, 1)]


def test_cleanup_never_changes_occupancy():
    cells = consensus_grid()
    cells[0][0] = cell(None, occupied=False)
    before = [[item.occupied for item in row] for row in cells]

    result = cleanup_cells(cells)

    assert [[item.occupied for item in row] for row in result.cells] == before
