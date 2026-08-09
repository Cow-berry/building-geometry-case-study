# Design note

> This is a template. Replace each section with your thinking. We read this first —
> it matters more than line count. Keep it sharp; bullet points are fine.

## Problem interpretation

> How you read the problem. What "massing under constraints" means to you, and the
> scope you chose to tackle (and not).

Massing uner constaints is meant to be used by architects to get rough estimation of the shape and metrics of the future building, if certain constraints were implemeneted. Some constraints could be hard set by the rules of the specific area, others the architect could vary to try aiming for different shapes and metrics.
Constraints can be either limits above or below, but generally the goal is to fit the largest structure that still fits into set limitations.

## Domain model

> The core types — site, constraints, massing/option — and how the saved options form
> a decision tree. Include the persistence schema (tables / relationships).

SitePolygon:
`points: list[list[int]]
: must be list of pairs of integers
: must have at least three points
: must be a valid non-intersecting polygon`

Constraint:
`setback: float
max_height: float
max_floor_count: int
floor_height: float
site_coverage_ratio: float
max_footprint_area: float | None
gfa_target: float | None
far_target: float | None`
: `site_coverage_ratio` is within (0,1]

MassingResult:
`
foorprint_points: list[list[float]]
footprint_area: float
setback: float
site_coverage_ratio
gfa: float
height: float
floor_count: int`

Massing:
`polygon: SitePolygon
constraint: Constraint
result: MassingResult
parent: Massing | None`


## Algorithm

> How you turn a site polygon + constraints into a massing: setback inset, floor
> stacking, metrics (footprint area, GFA, floor count), feasibility. Note the geometry
> library or approach and why.

- For inset calculation `shapely` library is used. For specific math problem like this it's a good practice to use an already existing mature library that already dealt with all the edge cases of degenerate polygons and reflex corners. This specific one can even give specific feedback to user about the problem with their polygon.
- One of the constraints, `site_coverage_ratio`, poses a challange. We want to set a setback such that the resulting footprint is a very specific portion of the site polygon area-wise. But setback on a polygon is not an obvious function on input parameters and can't be easily reversed to make this an 0(1) single formula problem. Luckily setback is a monotone function. So a simple way to resolve would be to find two value that are deinitively above and below the target. And then to just binary search the optimal setback. The lower value is the setback_distance we are given (that is probably set by the land rules). The above value is taken as largest distance between vertices because setting that as a setback would always yield a shape with 0 area. Additionally if the `max_footprint_area` constraint is set, inside the binary search we must also check if the resulting back doesn't cut enough area.
- For floor count there is an implicit hard limit on the number of floors set by `max_height` and `floor_to_floor_height`, so we have first cap it by that number.
- Since in real life context we can always assume the maximum number of floors is a small reasonable number, at this point we can just calculate the metrics for each floor count separately and work further with a list of options.
- Finally we have a `min_gross_footprint_area` to conside. It is either directly set by the `gross_footprint_area_target` or less directly by `floor_area_ratio_target` that still relates the same metrics. We can filter our options by purging anything that doesn't meet this minimum GFA. Finally we take the remaining option with the biggest number of floors and send it back to user.

## API contract

> The endpoints you exposed and their request/response shapes (create, branch, list,
> get, …).

`/db/ensure` -> void:
Initialises the database if it hasn't already been done

`massing/create/{points}/{constraints}/{parent}` -> {ok, massing_result}:
calculates a massing given the site polygon and constraints
on success of the massing algorithm, adds the massing parameters to the database, optionally setting the parent
returns the result of the massing algorithm

`massing/get/all` -> [{points, constraints, massing_result}]:
return a list of all saved massings


## Visualization

> What you render and why you chose that approach.

## Assumptions & trade-offs

> The decisions you made under ambiguity, and what you consciously traded away.
## Algorithm

Considering that targets like GFA and FAR can be "infeasible", that means that they are lower limits.
However the language being used is specifically "targets" which makes me think the algorithm needs to approach these lower limits as closely as possible.

In similar vein, I assume site coverage ratio is both a high limit and a target for optimization on the setback parameter.

## Decision Tree

I suppose even you repeat a position through a series of changes, you still want to get a new node in the decision tree. Jumping between nodes would potentially disrupt the flow

## Edge cases

> How you handle concave plots, an inset that collapses to zero/splits, infeasible
> constraint sets, self-intersection, an unreachable GFA target.

- Concave plots don't pose any additional problems, thank to `shapely` library taking careof insets in this case
- Inset that collapses to zero/splits is reported as such back to user as an error
- Infeasible constrain sets are detected early and reported in verbose manner
- Self intersection are detected by the `shapely` library and reported as such
- Unreachable GFA target is detected at the final step and reported as such

## What I'd do next

> With another week: what you'd build, in what order, and why.
