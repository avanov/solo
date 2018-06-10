from typing import Tuple, Generic


class Spec:
    def __and__(self, other: 'Spec') -> 'Spec':
        return And(self, other)

    def __or__(self, other: 'Spec') -> 'Spec':
        return Or(self, other)

    def __invert__(self) -> 'Spec':
        return Invert(self)

    def is_satisfied_by(self, other: Generic) -> bool:
        NotImplementedError()


class CompositeSpec(Spec):
    pass


class UnaryCompositeSpecification(CompositeSpec):
    def __init__(self, specification: Spec) -> None:
        self.specification = specification


class MultaryCompositeSpecification(CompositeSpec):
    def __init__(self, *specifications: Tuple[Spec]) -> None:
        self.specifications = specifications


class And(MultaryCompositeSpecification):
    def __and__(self, other: Spec) -> 'And':
        if isinstance(other, And):
            self.specifications += other.specifications
        else:
            self.specifications += (other,)

        return self

    def is_satisfied_by(self, other: Generic) -> bool:
        return all([specification.is_satisfied_by(other) for specification in self.specifications])


class Or(MultaryCompositeSpecification):
    def __or__(self, other: Spec) -> 'Or':
        if isinstance(other, Or):
            self.specifications += other.specifications
        else:
            self.specifications += (other,)

        return self

    def is_satisfied_by(self, other: Generic) -> bool:
        return any([specification.is_satisfied_by(other) for specification in self.specifications])


class Invert(UnaryCompositeSpecification):
    def is_satisfied_by(self, other: Generic) -> bool:
        return not self.specification.is_satisfied_by(other)
