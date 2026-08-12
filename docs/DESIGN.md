# Design note
## Problem interpretation

Massing uner constaints is meant to be used by architects to get rough estimation of the shape and metrics of the future building, if certain constraints were to be implemeneted. Some constraints could be hard set by the rules of the specific area, others the architect could vary to try aiming for different shapes and metrics.
Constraints can be either limits above or below, but generally the goal is to fit the largest structure that still fits into set limitations.

## Domain model
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
`polygon: SitePolygon [by id]
constraint: Constraint [by id]
result: MassingResult [by id]
parent: Massing | None [by id]`


## Algorithm

- For inset calculation `shapely` library is used. For specific math problem like this it's a good practice to use an already existing mature library that already dealt with all the edge cases of degenerate polygons and reflex corners. This specific one can even give specific feedback to user about the problem with their polygon.

- Achieving `site_coverage_ratio` is an optimization problem of finding specific value of a monotone function (footprint area is a monotone function of the setback), which can easily be solved with a binary search. For binary search have the low limit on setback at the `setback` parameter provided by user. For higher limit we take the diameter of the polygon, then binary search from there down to find the limit where the area becomes non-zero. And finally from there we can safely.
- For floor count there is an implicit hard limit on the number of floors set by `max_height` and `floor_to_floor_height`, so we have first cap it by that number.
- Since in real life context we can always assume the maximum number of floors is a small reasonable number, at this point we can just calculate the metrics for each floor count separately and work further with a list of options.
- Finally we have a `min_gross_footprint_area` to consider. It is either directly set by the `gross_footprint_area_target` or less directly by `floor_area_ratio_target` that still relates the same metrics. We can filter our options by purging anything that doesn't meet this minimum GFA. Finally we take the remaining option with the smallest GFA that fits the set limit.

## API contract

`/db/ensure` -> void:
Initialises the database if it hasn't already been done

`massing/create/{body: points constraints parent}` -> {ok, massing_result}:
calculates a massing given the site polygon and constraints
on success of the massing algorithm, adds the massing parameters to the database, optionally setting the parent
returns the result of the massing algorithm

`massing/get/all` -> [{points, constraints, massing_result}]:
return a list of all saved massings


## Visualization

First the Site Polygon is shown. The footprint is added to the same canvas when the massing is computed. 
It is shown to allow the architect user to visually confirm the site polygon is entered correctly, and to see the size and shape of the footprint compared to the site polygon, all from the bird eye's view.

The isometric projection of the 3d model of the building is shown on a separate canvas. The architext user needs some way to see the resulting 3d shape of the building. Isometric projection is specifically chosen because it involves the least amount of computation and is easier to implement.

Finally a interface is shown to navigate the decision tree.
The user gets two tables:
- One is for the current massing and its parents, and its parent's parent and so on.
- The other table is to show direct children of the current massing.
Clicking on any row allows the user to switch to that massing, and tweak parameters from there.
Aside from massing result and the number of children, each shows a small representation of the site polygon and the footprint, for easier navigation.

## Assumptions & trade-offs
### Algorithm

Considering that targets like GFA and FAR can be "infeasible", that means that they are lower limits.
However the language being used is specifically "targets" which makes me think the algorithm needs to approach these lower limits as closely as possible.

In similar vein, I assume site coverage ratio is both a high limit and a target for optimization on the setback parameter.

### Decision Tree

I suppose even you repeat a position through a series of changes, you still want to get a new node in the decision tree. Jumping between nodes would potentially disrupt the flow.

## Edge cases
- Concave plots don't pose any additional problems, thank to `shapely` library taking careof insets in this case
- Inset that collapses to zero/splits is reported as such back to user as an error
- Infeasible constrain sets are detected early and reported in verbose manner
- Self intersection are detected by the `shapely` library and reported as such
- Unreachable GFA target is detected at the final step and reported as such

## What I'd do next
Critical:
- Proper page design and layout
- User registration, should the system be hosted to many users from a single server
- Tab system to allow planning and switching between different projects

Better UX:
- Reodering and reshaping the tables based on the user feeback and what feels natural to tem
- Different 3D views if isometric does not meet the industry standart for massing
- Polygon input as a collapsible list of pairs of inputs if needed
- Ability to drag points around if needed
- Tree view of all decision nodes in a full tree digram
- Deleting subtrees if they are no longer needed
- Bookmarking certain decision nodes to get back to them
- Tweaking many massings from a single node without fully switching to the new ones, to quickly compare different directions in the table of children 
