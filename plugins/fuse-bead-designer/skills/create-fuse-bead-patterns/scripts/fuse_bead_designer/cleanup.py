"""Conservative, confidence-gated cleanup for sampled bead cells."""

from collections import Counter
from dataclasses import dataclass, replace
from statistics import median

from .quantize import SampledCell


@dataclass(frozen=True)
class CleanupResult:
    """The independently cleaned row-major cell grid and changed coordinates."""

    cells: list[list[SampledCell]]
    changed_cells: list[tuple[int, int]]


def cleanup_cells(
    cells: list[list[SampledCell]],
    protected_cells: frozenset[tuple[int, int]] | set[tuple[int, int]] = frozenset(),
) -> CleanupResult:
    """Replace only well-supported interior singleton colors.

    Decisions always use the original grid, so a replacement cannot trigger a
    second replacement during the same pass.  Empty cells are never changed.
    """
    width, height = _validate_grid(cells)
    protected = _validate_protected_cells(protected_cells)
    cleaned = [row.copy() for row in cells]
    changed: list[tuple[int, int]] = []
    for row in range(1, height - 1):
        for column in range(1, width - 1):
            coordinate = (column, row)
            current = cells[row][column]
            if coordinate in protected or not current.occupied:
                continue
            consensus, consensus_neighbors = _neighbor_consensus(cells, column, row)
            if consensus is None or current.color_id == consensus:
                continue
            neighbor_distance = median(neighbor.distance for neighbor in consensus_neighbors)
            assert current.distance is not None
            if current.distance < 1.5 * neighbor_distance:
                continue
            cleaned[row][column] = replace(current, color_id=consensus, distance=float(neighbor_distance))
            changed.append(coordinate)
    return CleanupResult(cleaned, changed)


def _validate_grid(cells: object) -> tuple[int, int]:
    if not isinstance(cells, list):
        raise ValueError("cells must be a list of rows")
    if not cells:
        return 0, 0
    if any(not isinstance(row, list) for row in cells):
        raise ValueError("cell rows must be lists")
    width = len(cells[0])
    if any(len(row) != width for row in cells):
        raise ValueError("cell rows must have equal lengths")
    if any(not isinstance(cell, SampledCell) for row in cells for cell in row):
        raise ValueError("cells must contain SampledCell instances")
    return width, len(cells)


def _validate_protected_cells(protected_cells: object) -> set[tuple[int, int]]:
    if not isinstance(protected_cells, (set, frozenset)):
        raise ValueError("protected_cells must be a set of coordinates")
    if any(
        not isinstance(coordinate, tuple)
        or len(coordinate) != 2
        or any(not isinstance(value, int) or isinstance(value, bool) for value in coordinate)
        for coordinate in protected_cells
    ):
        raise ValueError("protected_cells must contain integer coordinates")
    return set(protected_cells)


def _neighbor_consensus(
    cells: list[list[SampledCell]],
    column: int,
    row: int,
) -> tuple[str | None, list[SampledCell]]:
    neighbors = [
        cells[y][x]
        for y in range(row - 1, row + 2)
        for x in range(column - 1, column + 2)
        if (x, y) != (column, row) and cells[y][x].occupied
    ]
    counts = Counter(neighbor.color_id for neighbor in neighbors)
    if not counts:
        return None, []
    consensus, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    if count < 6:
        return None, []
    return consensus, [neighbor for neighbor in neighbors if neighbor.color_id == consensus]
