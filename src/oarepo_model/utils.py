import inspect


def add_to_class_list_preserve_mro(
    class_list: list[type], clz: type, prepend: bool = False
) -> None:
    if not inspect.isclass(clz):
        raise TypeError("Only classes can be added to ClassList")

    # Remove existing base class if it is a subclass of the new class
    for item in class_list:
        if issubclass(item, clz):
            # already an inherited class from this class is present, do nothing
            return

    # Choose enumeration direction based on insert_func
    idx = 0
    removed_positions = []
    while idx < len(class_list):
        item = class_list[idx]
        if issubclass(clz, item):
            removed_positions.append(idx)
            del class_list[idx]
        else:
            idx += 1

    if removed_positions:
        if prepend:
            # If we are prepending, we need to insert at the start
            class_list.insert(removed_positions[0], clz)
        else:
            class_list.insert(removed_positions[-1], clz)
    else:
        # If no class was removed, we append the new class
        if prepend:
            class_list.insert(0, clz)
        else:
            class_list.append(clz)

    # Ensure the order is consistent with MRO
    if is_mro_consistent(class_list):
        return

    values = list(class_list)
    class_list.clear()
    class_list.extend(make_mro_consistent(values))


def is_mro_consistent(class_list: list[type]) -> bool:
    try:
        # Directly attempt to create the MRO
        mro = type("_", tuple(class_list), {}).mro()
        # Check if our classes appear in the same order
        filtered_mro = [c for c in mro if c in class_list]
        return filtered_mro == class_list
    except TypeError:
        return False


def make_mro_consistent(class_list: list[type]) -> list[type]:
    if not class_list:
        return []

    # Start with the first class
    result = []
    result.append(class_list[0])

    try:
        for cls in class_list[1:]:
            # Find the best position to insert the current class
            insert_pos = len(result)

            # Check all possible positions from right to left
            for i in range(len(result), -1, -1):
                try:
                    # Test if inserting at position i would be valid
                    temp_order = result[:i] + [cls] + result[i:]
                    type("_", tuple(temp_order), {})
                    insert_pos = i
                    break
                except TypeError:
                    continue
            else:
                raise TypeError(
                    f"Cannot insert {cls} into MRO of {result}. "
                    "It would break the method resolution order."
                )

            # Insert at the found position
            result.insert(insert_pos, cls)
    except Exception as e:
        raise TypeError(
            f"Failed to make MRO consistent for {class_list}. "
            "Ensure that the classes are compatible."
        ) from e
    return result
