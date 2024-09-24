from typing import Callable, Optional


class PatternBasedMapper:
    @staticmethod
    def map_attributes(
        source: any,
        target: any,
        source_pattern: Optional[dict] = None,
        target_pattern: Optional[dict] = None,
        custom_mapping: Optional[dict[str, any]] = None,
        verbose: bool = False,
        transfer_values: bool = False,
        use_partial_matching: bool = True,
    ) -> dict[str, str]:
        """
        Map attributes from the source object to the target object based on defined patterns and optional custom mappings.

        Returns:
            dict[str, str]: A dictionary mapping source attribute names to target attribute names.
        """
        source_attrs = PatternBasedMapper._extract_attributes(source)
        target_attrs = PatternBasedMapper._extract_attributes(target)

        mapped_attributes = {}
        if custom_mapping:
            verified_mappings = PatternBasedMapper._verify_custom_mapping(source, target, custom_mapping)
            PatternBasedMapper._apply_custom_mapping(source, target, verified_mappings, transfer_values, verbose)
            mapped_attributes.update(verified_mappings)

        pattern_mapped_attributes = PatternBasedMapper._map_pattern_attributes(
            source_attrs, target_attrs, source, target, source_pattern, target_pattern, transfer_values, verbose
        )
        mapped_attributes.update(pattern_mapped_attributes)

        if use_partial_matching:
            partial_mapped_attributes = PatternBasedMapper._match_partial_attributes(
                source_attrs, target_attrs, source, target, transfer_values, verbose
            )
            mapped_attributes.update(partial_mapped_attributes)

        return mapped_attributes

    @staticmethod
    def _verify_custom_mapping(source: any, target: any, custom_mapping: dict[str, any]) -> dict[str, any]:
        """Verifies custom mappings and returns a dictionary of valid mappings."""
        verified_mappings = {}
        for s_attr, t_attr_info in custom_mapping.items():
            if isinstance(t_attr_info, tuple):
                t_attr, transformation = t_attr_info
            else:
                t_attr, transformation = t_attr_info, None

            if hasattr(source, s_attr) and hasattr(target, t_attr):
                verified_mappings[s_attr] = (t_attr, transformation)

        return verified_mappings

    @staticmethod
    def _apply_custom_mapping(
        source: any, target: any, verified_mappings: dict[str, any], transfer_values: bool = True, verbose: bool = False
    ) -> None:
        """Applies the verified custom mappings from the source to the target object."""
        for s_attr, t_attr_info in verified_mappings.items():
            if isinstance(t_attr_info, tuple):
                t_attr, transformation = t_attr_info
            else:
                t_attr, transformation = t_attr_info, None

            value = getattr(source, s_attr, None)

            if transformation and callable(transformation):
                value = transformation(value)

            if transfer_values:
                setattr(target, t_attr, value)
                if verbose:
                    print(f"Mapped {s_attr} from source to {t_attr} in target with value: {value}")

    @staticmethod
    def _map_pattern_attributes(
        source_attrs: list[str],
        target_attrs: list[str],
        source: any,
        target: any,
        source_pattern: Optional[dict],
        target_pattern: Optional[dict],
        transfer_values: bool = False,
        verbose: bool = False,
    ) -> dict[str, str]:
        """Maps attributes based on patterns defined for source and target attributes."""
        mapped_attributes = {}

        for s_attr in source_attrs:
            base_s_attr = PatternBasedMapper._strip_patterns(s_attr, source_pattern)

            for t_attr in target_attrs:
                base_t_attr = PatternBasedMapper._strip_patterns(t_attr, target_pattern)

                if base_s_attr == base_t_attr:
                    if transfer_values:
                        value = getattr(source, s_attr)
                        setattr(target, t_attr, value)
                        if verbose:
                            print(f"Mapped {s_attr} from source to {t_attr} in target with value: {value}")
                    mapped_attributes[s_attr] = t_attr
                    break

        return mapped_attributes

    @staticmethod
    def _match_partial_attributes(
        source_attrs: list[str],
        target_attrs: list[str],
        source: any,
        target: any,
        transfer_values: bool = False,
        verbose: bool = False,
    ) -> dict[str, str]:
        """Matches attributes based on partial naming conventions."""
        mapped_attributes = {}

        for s_attr in source_attrs:
            base_s_attr = s_attr

            for t_attr in target_attrs:
                base_t_attr = t_attr

                if any(seg in base_t_attr for seg in base_s_attr.split("_")) or any(
                    seg in base_s_attr for seg in base_t_attr.split("_")
                ):
                    if transfer_values:
                        value = getattr(source, s_attr)
                        setattr(target, t_attr, value)
                        if verbose:
                            print(f"Mapped {s_attr} from source to {t_attr} in target with value: {value}")
                    mapped_attributes[s_attr] = t_attr
                    break

        return mapped_attributes

    @staticmethod
    def _extract_attributes(obj: any) -> list[str]:
        """Extracts non-builtin attributes from the object."""
        return [attr for attr in dir(obj) if not attr.startswith("__") and not callable(getattr(obj, attr))]

    @staticmethod
    def _strip_patterns(attr: str, patterns: Optional[dict]) -> str:
        """Strips patterns like prefix and suffix from attribute names."""
        base_attr = attr
        if patterns:
            if patterns.get("prefix") and base_attr.startswith(patterns["prefix"]):
                base_attr = base_attr[len(patterns["prefix"]) :]
            if patterns.get("suffix") and base_attr.endswith(patterns["suffix"]):
                base_attr = base_attr[: -len(patterns["suffix"])]
        return base_attr

    @staticmethod
    def recursive_map(
        source: any,
        source_path: str,
        target: any,
        target_path: str,
        transformation: Optional[Callable] = None,
        verbose: bool = False,
    ) -> None:
        """Recursively maps attributes from source to target using specified paths."""
        source_segments = source_path.split(".")
        target_segments = target_path.split(".")

        current_source = source
        for segment in source_segments[:-1]:
            current_source = getattr(current_source, segment, None)
            if current_source is None:
                return  # Exit if the path is invalid

        current_target = target
        for segment in target_segments[:-1]:
            if not hasattr(current_target, segment) or getattr(current_target, segment) is None:
                setattr(current_target, segment, type("DynamicObject", (object,), {})())
            current_target = getattr(current_target, segment)

        final_source_attr = source_segments[-1]
        value = getattr(current_source, final_source_attr, None)

        if transformation:
            value = transformation(value)

        final_target_attr = target_segments[-1]
        setattr(current_target, final_target_attr, value)

        if verbose:
            print(f"Mapped {source_path} from source to {target_path} in target with value: {value}")
