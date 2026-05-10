Section 1: Sets
| Subsets |     | of  | Sets |     |     |     |     |     |     |     |
| ------- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
We use the notation P(A) to denote the set of all subsets of A and P (A) the set of all
k
subsets of A of size (or cardinality) k. We call P(A) “the set of all subsets of A” or simply
the power set of A. Let C(n,k) = |P (A)| denote the number of different k-subsets that
k
can be formed from an n-set. The notation n is also frequently used. These are called
|     |     |     |     |     |     |     | (cid:0) (cid:1) |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | --- | --- |
k
| binomial |     | coefficients |     | and are | read | “n choose | k.” We now | prove |     |     |
| -------- | --- | ------------ | --- | ------- | ---- | --------- | ---------- | ----- | --- | --- |
Theorem 2 (Binomial coefficient formula) The value of the binomial coefficient is
|     |     |     | (cid:18)n(cid:19) |           |     | n(n−1)···(n−k+1) |     |     | n!       |     |
| --- | --- | --- | ----------------- | --------- | --- | ---------------- | --- | --- | -------- | --- |
|     |     |     |                   | = C(n,k)= |     |                  |     | =   |          | ,   |
|     |     |     | k                 |           |     |                  | k!  |     | k!(n−k)! |     |
where 0! = 1 and, for j > 0, j! is the product of the first j integers. We read j! as “j
factorial”.
Proof: Let A be a set of size n. The elements of P (A) are sets and are thus unordered.
k
Generally speaking, unordered things are harder to count than ordered ones. Suppose,
instead of a set of size k chosen from A, you wanted to construct an ordered list L of k
elements from A (L is called a “k-list”). We could construct L in two stages.
• First choose an element of S ∈ P (A) (a subset of A with k elements). This can be
k
|     | done | in C(n,k) |     | ways since | C(n,k)= |     | |P (A)|. |     |     |     |
| --- | ---- | --------- | --- | ---------- | ------- | --- | -------- | --- | --- | --- |
k
| •   |     |     |     |     |     |     |     |     | k(k−1)···1 |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --- |
Next order S to obtainL. This orderingcan be donein k! = ways. Why?
You have k choices for the element of S to appear first in the list L, k−1 choices for
|     | the | next element, |     | k−2 | choices | for the | next element, | etc. |     |     |
| --- | --- | ------------- | --- | --- | ------- | ------- | ------------- | ---- | --- | --- |
Fromthistwo-stageprocess,weseethatthereareC(n,k)k!orderedk-listswithnorepeats.
(The factor C(n,k) is the number of ways to carry out the first stage and the factor k! is
| the | number | of  | ways | to carry | out | the second | stage.) |     |     |     |
| --- | ------ | --- | ---- | -------- | --- | ---------- | ------- | --- | --- | --- |
Theorem 3 (Number of ordered lists) The number of ordered k-lists L that can be
| made | from | and | n-set | A is |     |     |     |     |     |     |
| ---- | ---- | --- | ----- | ---- | --- | --- | --- | --- | --- | --- |
nk
|     | •   | if repeats |     | are allowed |     | and |     |     |     |     |
| --- | --- | ---------- | --- | ----------- | --- | --- | --- | --- | --- | --- |
• n(n−1)···(n−k+1)= n!/(n−k)! if repeats are not allowed. One also uses the
notation (n) for these values. This is called the “falling factorial” and is read “n
k
|     |     | falling | k”. |     |     |     |     |     |     |     |
| --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
Why? With repeats allowed, there are n choices of elements in A for the first entry
in the k-list L, n choices for the second entry, etc. If repeats are not allowed, there are
n choices of elements in A for the first entry in the k-list L, n−1 choices for the second
entry, etc.
SF-9
