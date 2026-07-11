import statistics


def classify_color(focus_median, red_threshold=30.0, green_threshold=60.0):
    if focus_median >= green_threshold:
        return "g"
    if focus_median <= red_threshold:
        return "r"
    return "b"


def assign_regions(students, num_regions):
    valid = [
        (s["position"], s["focus_score"])
        for s in students
        if s.get("position") is not None and s.get("focus_score") is not None
    ]
    regions = {i: [] for i in range(num_regions)}
    if not valid:
        return regions

    positions = [p for p, _ in valid]
    min_pos = min(positions)
    max_pos = max(positions)
    span = max_pos - min_pos if max_pos > min_pos else 1.0

    for pos, score in valid:
        region_id = min(num_regions - 1, int((max_pos - pos) / span * num_regions))
        regions[region_id].append(score)

    return regions


def compute_region_colors(regions, red_threshold=30.0, green_threshold=60.0):
    result = []
    for region_id in sorted(regions.keys()):
        scores = regions[region_id]
        if not scores:
            result.append({"region": region_id, "color": "off", "median": None, "count": 0})
        else:
            median = statistics.median(scores)
            result.append(
                {
                    "region": region_id,
                    "color": classify_color(median, red_threshold, green_threshold),
                    "median": round(median, 1),
                    "count": len(scores),
                }
            )
    return result


class RegionFocusEngine:
    def __init__(self, num_regions=5, red_threshold=30.0, green_threshold=60.0):
        self.num_regions = num_regions
        self.red_threshold = red_threshold
        self.green_threshold = green_threshold
        self._last_state = [{"region": i, "color": "off", "median": None, "count": 0} for i in range(num_regions)]

    def update(self, students_data, now):  # noqa: ARG002
        regions = assign_regions(students_data, self.num_regions)
        self._last_state = compute_region_colors(regions, self.red_threshold, self.green_threshold)
        return self._last_state

    def get_region_state(self):
        return list(self._last_state)
