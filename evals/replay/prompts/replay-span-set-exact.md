Context packs hide a parent memory when all of its passage spans were retrieved. The check counts the spans against the total they declare, so spans with indices 0, 2 and 9 and a declared total of 3 hide the parent while the middle of the body is missing. Spans left over from an earlier projection of the same memory can also disagree about the total.

Hide the parent only when every retrieved span agrees on the total and the indices are exactly 0 through total minus 1.
