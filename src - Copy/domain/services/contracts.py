from __future__ import annotations

from abc import ABC, abstractmethod

from elecgenflow.domain.contracts.candidate import DesignCandidate
from elecgenflow.domain.contracts.problem import DesignProblem


class CandidateGenerator(ABC):
    @abstractmethod
    def generate(self, problem: DesignProblem) -> list[DesignCandidate]:
        raise NotImplementedError

    @staticmethod
    def stub() -> CandidateGenerator:
        return _StubCandidateGenerator()


class RuleEngine(ABC):
    @abstractmethod
    def apply(self, candidate: DesignCandidate) -> DesignCandidate:
        raise NotImplementedError

    @staticmethod
    def stub() -> RuleEngine:
        return _StubRuleEngine()


class SimulationEngine(ABC):
    @abstractmethod
    def simulate(self, candidate: DesignCandidate) -> DesignCandidate:
        raise NotImplementedError

    @staticmethod
    def stub() -> SimulationEngine:
        return _StubSimulationEngine()


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, candidate: DesignCandidate) -> DesignCandidate:
        raise NotImplementedError

    @staticmethod
    def stub() -> Evaluator:
        return _StubEvaluator()


class Optimizer(ABC):
    @abstractmethod
    def rank(self, candidates: list[DesignCandidate]) -> list[DesignCandidate]:
        raise NotImplementedError

    @staticmethod
    def stub() -> Optimizer:
        return _StubOptimizer()


# -------------------------
# Stub implementations (EPIC-1)
# -------------------------


class _StubCandidateGenerator(CandidateGenerator):
    def generate(self, problem: DesignProblem) -> list[DesignCandidate]:
        return [DesignCandidate.from_problem(problem, candidate_id="CAND-0001")]


class _StubRuleEngine(RuleEngine):
    def apply(self, candidate: DesignCandidate) -> DesignCandidate:
        return candidate


class _StubSimulationEngine(SimulationEngine):
    def simulate(self, candidate: DesignCandidate) -> DesignCandidate:
        return candidate


class _StubEvaluator(Evaluator):
    def evaluate(self, candidate: DesignCandidate) -> DesignCandidate:
        return candidate


class _StubOptimizer(Optimizer):
    def rank(self, candidates: list[DesignCandidate]) -> list[DesignCandidate]:
        return candidates
