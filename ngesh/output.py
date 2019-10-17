# encoding: utf-8

"""
Module with auxiliary function for text generation.
"""

# Import Python standard libraries
import itertools


def tree2wordlist(tree):
    """
    Returns a string with the representation of a tree in wordlist format.
    """

    # The number of characters for each taxon; it will be set when the
    # first taxon data is read.
    num_chars = None

    # Buffer for the data to be returned
    buf = ["Language_ID,Feature_ID,Value"]

    # Iterate over all leaves
    for leave in tree.get_leaves():
        # Get the number of characters if necessary
        if not num_chars:
            num_chars = len(leave.chars)

        # Iterate over all characters of the current leave
        rows = [
            [leave.name, "feature_%i" % idx, str(leave.chars[idx])]
            for idx in range(num_chars)
        ]

        # Add all rows as comma-separated strings to the buffer; while this
        # would work without assignment, it is best pratice to always
        # assign an expression to something.
        _ = [buf.append(",".join(row)) for row in rows]

    # Join the buffer and return it
    return "\n".join(buf)


def tree2nexus(tree):
    """
    Returns a string with the representation of a tree in NEXUS format.

    Parameters
    ----------

    tree : ete3
        The ete3 tree whose NEXUS representation will be returned.

    Returns
    -------

    buf : string
        A string with the full representation of the tree in NEXUS format.
    """

    # Collect all taxa and their characters, provided the characters
    # exist
    try:
        data = {leaf.name: leaf.chars for leaf in tree.get_leaves()}
        missing_chars = False
    except AttributeError:
        data = {leaf.name: [] for leaf in tree.get_leaves()}
        missing_chars = True

    # Collect the number of states used per concept in the entire tree.
    concept_states = [set(concept) for concept in itertools.zip_longest(*data.values())]

    # Build the textual binary strings
    bin_strings = {}
    for taxon, char in data.items():
        # Build a sequence of booleans indicating whether the state is found
        seq = itertools.chain.from_iterable(
            [
                [concept_state == state for state in concept_states[concept_idx]]
                for concept_idx, concept_state in enumerate(char)
            ]
        )

        # Map the `seq`uence to a binary string
        bin_strings[taxon] = "".join(["01"[value] for value in seq])

    # Get the length of the longest taxon name for alignment
    # NOTE: This will result in `align_string` being something like "%-24s %s",
    #       guaranteeing left alignment of the taxa name and strings of
    #       characters starting at the same column.
    max_len = max([len(name) for name in data])
    align_string = "%%-%is %%s" % (max_len + 3)

    # Build the buffer string holding the entire NEXUS file.
    buf = ["#NEXUS", ""]

    if missing_chars:
        buf.append("[WARNING: characters missing from tree]\n")

    buf.append("begin data;")
    buf.append(
        "  dimensions ntax=%i nchar=%i;"
        % (len(bin_strings), len(list(bin_strings.values())[0]))
    )
    buf.append("  format datatype=standard missing=? gap=-;")
    buf.append("  matrix")

    for taxon, bin_string in bin_strings.items():
        buf.append(align_string % (taxon.replace(" ", "_"), bin_string))

    buf.append("  ;")
    buf.append("end;")

    # Join the buffer and return it
    return "\n".join(buf)
