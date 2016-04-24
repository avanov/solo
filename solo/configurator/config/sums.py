import re
import venusian
from typing import Dict, Any
from collections import OrderedDict

from ..exceptions import ConfigurationError


SUM_TYPE_VARIANT_NAME_RE = re.compile('^[A-Z][0-9A-Z_]*$')


class SumVariant:
    venusian = venusian

    def __init__(self, variant_of, name: str, value):
        """

        :param variant_of: class of the SumType this variant instance belongs to
        :param name: name of the variant, as it is defined in the source code (uppercase)
        :param value: variant value
        """
        self.variant_of = variant_of
        self.name = name
        self.value = value

    def is_primitive_type(self):
        if isinstance(self.value, str):
            primitive_type = True
        elif isinstance(self.value, int):
            primitive_type = True
        else:
            primitive_type = False
        return primitive_type


    def __call__(self, category: str):
        """ This method is called when we declare variant cases. For instance:

            >>> class Language(SumType):
            >>>     ENGLISH = 'en'
            >>>
            >>> @Language.ENGLISH(category='category_name')
            >>> def category_implementation():
            >>>     pass
            >>>

        :param category: name of the category
        """
        categories_dict = self.variant_of.__sum_meta__.categories
        other_variants = self.variant_of.__sum_meta__.variants

        categories_dict.setdefault(category, {v: None for v in other_variants})

        def wrapper(wrapped):
            def callback(scanner, name, obj):
                """ This method will be called by venusian.
                The ``callback`` name is not reserved, we just pass this callable
                to ``self.venusian.attach()`` below. Although, callback's arguments list is strictly defined.
                """
                categories_dict = self.variant_of.__sum_meta__.categories
                case_implementations = categories_dict[category]
                if case_implementations[self.name] is not None:
                    # venusian may scan the same declarations multiple times during the app initialization,
                    # therefore we allow re-assignment of the same case implementations and prohibit
                    # any new implementations
                    if case_implementations[self.name] is not obj:
                        raise TypeError(
                            'Variant {variant} of {type} is already bound to the category {category} => {impl}. '
                            'Conflict at {target}'.format(
                                variant=self.name,
                                type=self.variant_of.__sum_meta__.type,
                                category=category,
                                impl=str(case_implementations[self.name]),
                                target=str(obj)
                            )
                        )
                case_implementations[self.name] = obj
                # Re-calculate matches
                self.variant_of.__sum_meta__.matches = {
                    variant: {case: impl[variant] for case, impl in categories_dict.items()}
                    for variant in self.variant_of.__sum_meta__.variants
                }
                scanner.config.sums.update_sum_type_registry(self.variant_of.__sum_meta__)

            info = self.venusian.attach(wrapped, callback, category='solo')
            return wrapped
        return wrapper


class SumTypeMetaData:
    __slots__ = ('type', 'variants', 'values', 'categories', 'matches')
    def __init__(self, type, variants: Dict[str, SumVariant], values, categories: Dict[Any, Any], matches: Dict[str, Dict[Any, Any]]):
        self.type = type
        self.variants = variants
        self.values = values
        self.categories = categories
        self.matches = matches


class SumTypeMetaclass(type):
    """ Metaclass object to be used with the actual SumType implementation.
    """
    def __new__(mcs, class_name: str, bases, attrs: Dict[str, Any]):
        """ This magic method is called when a new SumType class is being defined and parsed.
        """
        cls = type.__new__(mcs, class_name, bases, attrs)

        variants = {}
        for attr_name, value in attrs.items():
            if not SUM_TYPE_VARIANT_NAME_RE.match(attr_name):
                continue
            variant = SumVariant(variant_of=cls, name=attr_name, value=value)
            setattr(cls, attr_name, variant)
            variants[attr_name] = variant

        values = {attrs[variant_name]: variant_name for variant_name in variants}
        cls.__sum_meta__ = SumTypeMetaData(
            type=cls,
            # set of SumType variants
            variants=variants,
            # dict of value => variant mappings
            values=values,
            categories={},
            # dict of value => match instances.
            # Used by .match() for O(1) result retrieval
            matches={v: {} for v in variants}
        )
        return cls

    # Make the object iterable, similar to the standard enum.Enum
    def __iter__(cls):
        return cls.__sum_meta__.variants.values().__iter__()


class SumType(metaclass=SumTypeMetaclass):
    __sum_meta__ = None  # type: SumTypeMetaData

    class Mismatch(Exception):
        pass

    class PatternError(Exception):
        pass

    @classmethod
    def values(cls):
        return set(cls.__sum_meta__.values.keys())

    @classmethod
    def match(cls, value):
        """
        :rtype: dict or :class:`types.FunctionType`
        """
        variant = None
        for variant_name, variant_type in cls.__sum_meta__.variants.items():
            if variant_type.is_primitive_type():
                # We compare primitive types with equality matching
                if value == variant_type.value:
                    variant = variant_name
                    break
            else:
                # We compare non-primitive types with type checking
                if isinstance(value, variant_type.value):
                    variant = variant_name
                    break

        if variant is None:
            raise cls.Mismatch(
                u'Variant value "{value}" is not a part of the type {type}: {values}'.format(
                    value=value,
                    type=cls.__sum_meta__.type,
                    values=u', '.join(['{val} => {var}'.format(val=val, var=var)
                                       for val, var in cls.__sum_meta__.values.items()])
                )
            )

        return cls.__sum_meta__.matches[variant]

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
                u'Variant value "{value}" is not a part of the type {type}: {values}'.format(
                    value=value,
                    type=cls.__sum_meta__.type,
                    values=u', '.join(['{val} => {var}'.format(val=val, var=var)
                                       for val, var in cls.__sum_meta__.values.items()])
                )
            )
        return matcher

    def __init__(self):
        raise TypeError('SumType is a type, not an instance.')


class SumTypesConfigurator:

    def __init__(self):
        self.sum_types = OrderedDict()  # type: Dict[str, SumTypeMetaData]

    def update_sum_type_registry(self, sum_type_meta: SumTypeMetaData):
        self.sum_types[sum_type_meta.type] = sum_type_meta

    def check_sum_types_consistency(self, package):
        for obj_id, sum_type_meta in self.sum_types.items():
            for category_name, category_meta in sum_type_meta.categories.items():
                for variant, implementation in category_meta.items():
                    if implementation is None:
                        raise ConfigurationError(
                            'Category "{category_name}" of the sum type {type} is not exhaustive. '
                            'Here is the missing variant: {variant} '
                            .format(
                                category_name=category_name,
                                type=sum_type_meta.type,
                                variant='{}.{}'.format(sum_type_meta.type.__name__, variant)
                            )
                        )
