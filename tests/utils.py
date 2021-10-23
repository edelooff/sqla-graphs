def get_edge_labels(edge):
    """Returns a mapping of node name to edge label given an edge mapping."""
    tail, head = map(normalize, edge["points"])
    return {
        head: normalize(edge["attributes"].get("headlabel", "")),
        tail: normalize(edge["attributes"].get("taillabel", "")),
    }


def normalize(string):
    """Returns a string without outer quotes or whitespace."""
    return string.strip("'\" ")
