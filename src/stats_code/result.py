from .language_config import Language

Stats = dict[Language, int]


class RepoStatsNode:
    """
    A repo node in the stats-code result tree.
    """

    def __init__(self) -> None:
        self.submodules: dict[str, RepoStatsNode] = {}
        self.stats: Stats = {}


class Result:
    """
    A class to represent the result of the result of stats-code.
    It contains the overall statistics for the repository.
    """

    def __init__(self) -> None:
        self._tree_root: RepoStatsNode = RepoStatsNode()

    @property
    def total(self) -> Stats:
        return self.reduce_from_node(self._tree_root)

    @property
    def root_repo(self) -> RepoStatsNode:
        return self._tree_root

    @staticmethod
    def get_submodules(node: RepoStatsNode) -> dict[str, RepoStatsNode]:
        return node.submodules

    @staticmethod
    def reduce_from_node(node: RepoStatsNode) -> Stats:
        aggregated_stats: Stats = dict(node.stats)  # start with current node's stats
        for submodule in node.submodules.values():
            submodule_stats = Result.reduce_from_node(submodule)
            for lang, count in submodule_stats.items():
                aggregated_stats[lang] = aggregated_stats.get(lang, 0) + count
        return aggregated_stats
