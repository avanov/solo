import logging
import re
from collections import OrderedDict
from typing import Dict, Any, get_type_hints, Type, Iterator, Set, NamedTuple

import venusian

from ..exceptions import ConfigurationError


log = logging.getLogger(__name__)


SUM_TYPE_VARIANT_NAME_RE = re.compile('^[A-Z][0-9A-Z_]*$')


class ProxyContract:
    def __init__(self, parent: 'SumVariant') -> None:
        # We reference the parent and not the parent's contract attribute, because
        # this attribute may be replaced during app initialisation (NamedTuple._replace)
        self.parent = parent

    def __getattr__(self, item):
        return getattr(self.parent.contract, item)


class SumVariant:
    venusian = venusian

    def __init__(self,
                 variant_of: Type['SumType'],
                 name: str,
                 constructor,
                 value,
                 contract: NamedTuple) -> None:
        """
        :param variant_of: class of the SumType this variant instance belongs to
        :param name: name of the variant, as it is defined in the source code (uppercase)
        :param value: variant value
        :param constructor: constructor for a data that this variant can hold
        :param contract: bound terms, will be empty most of the time, and present in constructor only for
        replicating them when SumVariantInstance is created from base SumVariant
        """
        self.variant_of = variant_of
        self.name = name
        self.value = value
        self.constructor = constructor
        self.contract = contract
        # A proxy object to imitate access through SumType.Contract
        # Exists only for the sake of satisfying PyCharm type checker
        self.Contract = ProxyContract(self)

    def is_primitive_type(self) -> bool:
        return self.constructor in (int, str, float, bool)

    def __call__(self, *data_args, **data_kwargs) -> 'SumVariantInstance':
        """ Returns a data-holding variant"""
        return SumVariantInstance(data_args,
                                  data_kwargs,
                                  variant_of=self.variant_of,
                                  name=self.name,
                                  constructor=self.constructor,
                                  value=self.value,
                                  contract=self.contract)

    def __eq__(self, other: 'SumVariant') -> bool:
        """ This method is redefined only to simplify variant comparison for tests with mocks that
        might do things like mocked_function.assert_called_with(SumType.VARIANT)
        """
        return all([
            self.variant_of is other.variant_of,
            self.name == other.name,
            self.value == other.value,
            self.constructor == other.constructor,
            self.contract == other.contract
        ])

    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    # If a class that overrides __eq__() needs to retain the implementation of __hash__() from a parent class,
    # the interpreter must be told this explicitly by setting __hash__ = <ParentClass>.__hash__
    __hash__ = object.__hash__

    def bind(self, contract_term: str) -> Any:
        """ This method is called when we declare variant cases. For instance:
            >>> class Language(SumType):
            >>>     ENGLISH = 'en'
            >>>
            >>> @Language.ENGLISH.bind('term_name')
            >>> def term_implementation():
            >>>     pass
            >>>
        :param contract_term: name of the term
        """
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)

        def wrapper(wrapped):
            def callback(scanner, name, obj):
                """ This method will be called by venusian.
                The ``callback`` name is not reserved, we just pass this callable
                to ``self.venusian.attach()`` below. Although, callback's arguments list is strictly defined.
                """
                attr = settings.get('attr')
                if attr:  # check whether a decorated object is something inside a class scope
                    obj = getattr(obj, attr)

                previous_term = getattr(self.contract, contract_term)
                if previous_term is not None:
                    # venusian may scan the same declarations multiple times during the app initialization,
                    # therefore we allow re-assignment of the same case implementations and prohibit
                    # any new implementations
                    if previous_term is not obj:
                        raise TypeError(
                            'Variant {variant} already has a contract term "{contract_term}" => {impl}. '
                            'It conflicts with {target}'.format(
                                variant=f'{self.variant_of.__sum_meta__.type.__module__}.{self.variant_of.__sum_meta__.type.__name__}::{self.name}',
                                contract_term=contract_term,
                                impl=f'{previous_term.__module__}:{previous_term.__name__}',
                                target=f'{obj.__module__}:{obj.__name__}'
                            )
                        )

                self.contract = self.contract._replace(**{contract_term: obj})

                # Re-calculate matches
                self.variant_of.__sum_meta__.matches = {
                    variant: {case: impl for case, impl in self.contract._asdict().items()}
                    for variant in self.variant_of.__sum_meta__.variants
                }
                scanner.configurator.sums.update_sum_type_registry(self.variant_of.__sum_meta__)

            info = self.venusian.attach(wrapped, callback, category='frameapp_namespace', depth=depth + 1)
            if info.scope == 'class':
                # if the decorator was attached to a method in a class, or
                # otherwise executed at class scope, we need to set an
                # 'attr' into the settings if one isn't already in there
                if settings.get('attr') is None:
                    settings['attr'] = wrapped.__name__
            return wrapped
        return wrapper

    def __repr__(self) -> str:
        return 'SumVariant(type={}.{}, name={}, value={})'.format(self.variant_of.__module__, self.variant_of.__name__, self.name, self.value)


class SumVariantInstance(SumVariant):
    """ A SumVariant that holds data associated with it
    """
    def __init__(self, data_args, data_kwargs, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data = self.constructor(*data_args, **data_kwargs)

    def __eq__(self, other: SumVariant) -> bool:
        return super().__eq__(other) and self.data == getattr(other, 'data', None)

    __hash__ = SumVariant.__hash__

    def __repr__(self) -> str:
        return f'SumVariantInstance(type={self.variant_of.__module__}.{self.variant_of.__name__}, name={self.name}, value={self.value}, data={self.constructor})'


class SumTypeMetaData:
    __slots__ = ('type', 'variants', 'values', 'contract', 'matches')

    def __init__(self,
                 type,
                 variants: Dict[str, SumVariant],
                 values: Dict[str, str],
                 contract: NamedTuple,
                 matches: Dict[str, Dict[Any, Any]]) -> None:
        self.type = type
        self.variants = variants
        self.values = values
        self.contract = contract
        self.matches = matches


class SumTypeMetaclass(type):
    """ Metaclass object to be used with the actual SumType implementation.
    """
    def __new__(mcs, class_name: str, bases, attrs: Dict[str, Any]):
        """ This magic method is called when a new SumType class is being defined and parsed.
        """
        cls = type.__new__(mcs, class_name, bases, attrs)

        variants = {}
        variant_values = {}
        variant_constructors = get_type_hints(cls)

        # 0. Create a Contract, if specified
        # --------------------------------------------------
        try:
            contract_prototype = attrs['Contract']
        except KeyError:
            terms = {}
            contract_class: Type[NamedTuple] = NamedTuple(f'{class_name}Contract')
        else:
            terms = get_type_hints(contract_prototype)
            contract_class: Type[NamedTuple] = NamedTuple(f'{class_name}Contract', terms.items())

        contract = contract_class(**{k: None for k in terms.keys()})

        # 1. Populating variants from long-form definitions:
        #    class A(SumType):
        #        B[: type] = value
        # --------------------------------------------------
        for attr_name, value in attrs.items():
            # Populating variants from long-form definitions:
            # class A(SumType):
            #     B[: type] = value
            if not SUM_TYPE_VARIANT_NAME_RE.match(attr_name):
                continue

            if attr_name not in variant_constructors:
                raise ConfigurationError(f'SumType Variant "{cls.__module__}::{cls.__name__}::{attr_name}" '
                                         "must have a value constructor. "
                                         "You need to specify it as a type hint.")

            variant = SumVariant(variant_of=cls,
                                 name=attr_name,
                                 constructor=variant_constructors[attr_name],
                                 value=value,
                                 contract=contract)

            setattr(cls, attr_name, variant)
            variants[attr_name] = variant
            variant_values[value] = attr_name

        # 2. Populating variants from short-form definitions:
        #    class A(SumType):
        #        B: type
        # --------------------------------------------------
        # note that the value will be a lower-case version of the variant name
        for attr_name, constructor in variant_constructors.items():
            if not SUM_TYPE_VARIANT_NAME_RE.match(attr_name):
                continue
            if attr_name in variants:
                continue

            value = attr_name.lower()
            variant = SumVariant(variant_of=cls,
                                 name=attr_name,
                                 constructor=variant_constructors[attr_name],
                                 value=value,
                                 contract=contract)

            setattr(cls, attr_name, variant)
            variants[attr_name] = variant
            variant_values[value] = attr_name

        # 4. Let's create an instance of the contract and use it for replacement of the original
        # class definition. This will allow us to use SumType.Contract in bindings like:
        #
        # >>> @SomeSumType.VARIANT.bind(SomeSumType.Contract.contract_term)
        # >>> def some_term():
        # >>>     pass
        #
        # It is useful for "Find Usages" functionality of PyCharm
        # --------------------------------------------------------------------------------------
        c = contract_class(**{t: t for t in contract._fields})
        setattr(cls, 'Contract', c)

        # 5. Finalize
        # --------------------------------------------------
        cls.__sum_meta__ = SumTypeMetaData(
            type=cls,
            # set of SumType variants
            variants=variants,
            # dict of value => variant mappings
            values=variant_values,
            contract=contract,
            # dict of value => match instances.
            # Used by .match() for O(1) result retrieval
            matches={v: {} for v in variants}
        )
        return cls

    # Make the object iterable, similar to the standard enum.Enum
    def __iter__(cls) -> Iterator:
        return cls.__sum_meta__.variants.values().__iter__()


class SumType(metaclass=SumTypeMetaclass):
    __sum_meta__: SumTypeMetaData = None

    class Mismatch(Exception):
        pass

    class PatternError(Exception):
        pass

    @classmethod
    def values(cls) -> Set:
        return set(cls.__sum_meta__.values.keys())

    @classmethod
    def match(cls, value) -> SumVariant:
        """
        :rtype: dict or :class:`types.FunctionType`
        """
        variant = None
        for variant_name, variant_type in cls.__sum_meta__.variants.items():
            if variant_type.is_primitive_type():
                # We compare primitive types with equality matching
                if value == variant_type.value:
                    variant = variant_type
                    break
            else:
                # We compare non-primitive types with type checking
                if isinstance(value, variant_type.value):
                    variant = variant_type
                    break

        if variant is None:
            raise cls.Mismatch(
                'Variant value "{value}" is not a part of the type {type}: {values}'.format(
                    value=value,
                    type=cls.__sum_meta__.type,
                    values=u', '.join(['{val} => {var}'.format(val=val, var=var)
                                       for val, var in cls.__sum_meta__.values.items()])
                )
            )

        return variant

    @classmethod
    def inline_match(cls, **inline_cases):
        all_cases = set(cls.__sum_meta__.variants.keys())
        inline_cases = inline_cases.items()
        checked_cases = []
        for variant_name, fun in inline_cases:
            try:
                variant = cls.__sum_meta__.variants[variant_name]
            except KeyError:
                raise cls.PatternError(
                    'Variant {variant} does not belong to the type {type}'.format(
                        variant=str(variant_name),
                        type=cls.__sum_meta__.type,
                    )
                )
            all_cases.remove(variant.name)
            checked_cases.append((variant, fun))

        if all_cases:
            raise cls.PatternError(
                'Inline cases are not exhaustive.\n'
                'Here is the variant that is not matched: {variant} '.format(
                    variant=list(all_cases)[0]
                )
            )

        def matcher(value):
            for variant, fun in checked_cases:
                if variant.is_primitive_type():
                    if value == variant.value:
                        return fun
                else:
                    if isinstance(value, variant.value):
                        return fun

            raise cls.Mismatch(
                'Variant value "{value}" is not a part of the type {type}: {values}'.format(
                    value=value,
                    type=cls.__sum_meta__.type,
                    values=u', '.join(['{val} => {var}'.format(val=val, var=var)
                                       for val, var in cls.__sum_meta__.values.items()])
                )
            )
        return matcher

    def __init__(self) -> None:
        raise TypeError('SumType is a type, not an instance.')


class SumTypesConfigurator:

    def __init__(self) -> None:
        self.registry = OrderedDict()

    def update_sum_type_registry(self, sum_type_meta: SumTypeMetaData) -> None:
        self.registry[sum_type_meta.type] = sum_type_meta

    def check_sum_types_consistency(self, namespace: str) -> None:
        for obj_id, sum_type_meta in self.registry.items():
            for variant_name, variant in sum_type_meta.variants.items():
                for contract_term, implementation in variant.contract._asdict().items():
                    if implementation is None:
                        raise ConfigurationError(
                            'Contract term "{contract_term}" of the sum type {type} is not complete. '
                            'Here is the missing variant: {variant} '
                            .format(
                                contract_term=contract_term,
                                type=f'{sum_type_meta.type.__module__}.{sum_type_meta.type.__name__}',
                                variant=f'{sum_type_meta.type.__module__}.{sum_type_meta.type.__name__}::{variant_name}'
                            )
                        )
            log.debug(f'Checked for {sum_type_meta.type.__module__}.{sum_type_meta.type.__name__}. '
                      f'Registered contract: {sum_type_meta.contract}')
