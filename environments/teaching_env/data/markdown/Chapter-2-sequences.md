2C H A P T E R

...........................................

Sequences

§7 Limits of Sequences

A sequence is a function whose domain is a set of the form {n ∈ Z :
n ≥ m}; m is usually 1 or 0. Thus a sequence is a function that
has a speciﬁed value for each integer n ≥ m. It is customary to de-
note a sequence by a letter such as s and to denote its value at n
as sn rather than s(n). It is often convenient to write the sequence
as (sn)∞
n=m or (sm, sm+1, sm+2, . . .). If m = 1 we may write (sn)n∈N
or of course (s1, s2, s3, . . .). Sometimes we will write (sn) when the
domain is understood or when the results under discussion do not
depend on the speciﬁc value of m. In this chapter, we will be inter-
ested in sequences whose range values are real numbers, i.e., each sn
represents a real number.

Example 1
(a) Consider the sequence (sn)n∈N where sn = 1
16 , 1

sequence (1, 1
function with domain N whose value at each n is 1
of values is {1, 1
25 , . . .}.

n2 . This is the
25 , . . .). Formally, of course, this is the
n2 . The set

16 , 1

9 , 1

9 , 1

4 , 1

4 , 1

K.A. Ross, Elementary Analysis: The Theory of Calculus,
Undergraduate Texts in Mathematics, DOI 10.1007/978-1-4614-6271-2 2,
© Springer Science+Business Media New York 2013

33

34

2. Sequences

(b) Consider the sequence given by an = (−1)n for n ≥ 0, i.e.,
(an)∞
n=0 where an = (−1)n. Note that the ﬁrst term of the se-
quence is a0 = 1 and the sequence is (1, −1, 1, −1, 1, −1, 1, . . .).
Formally, this is a function whose domain is {0, 1, 2, . . .} and
whose set of values is {−1, 1}.

It is important to distinguish between a sequence and its
set of values, since the validity of many results in this book
depends on whether we are working with a sequence or a set.
We will always use parentheses ( ) to signify a sequence and
braces { } to signify a set. The sequence given by an = (−1)n
has an inﬁnite number of terms even though their values are
repeated over and over. On the other hand, the set {(−1)n :
n = 0, 1, 2, . . .} is exactly the set {−1, 1} consisting of two
numbers.

(c) Consider the sequence cos( nπ

sequence is cos( π
2 , −1, − 1
2 , − 1
( 1
The set of values is {cos( nπ

3 ) = cos 60◦ = 1
2 , 1, 1
2 , 1

3 ), n ∈ N. The ﬁrst term of this
2 and the sequence looks like
2 , − 1
2 , − 1
√
2, 3

2 , −1, − 1
2 , − 1
2 , 1, 1
3 ) : n ∈ N} = { 1
√

2 , −1, 1}.
√
3, 4

2 , −1, . . .).

2 , 1

n, n ∈ N, the sequence is (1,

4, . . .). If we
approximate values to four decimal places, the sequence looks
like

√
(d) If an = n

(1, 1.4142, 1.4422, 1.4142, 1.3797, 1.3480, 1.3205, 1.2968, . . .).

It turns out that a100 is approximately 1.0471 and a1,000 is
approximately 1.0069.

(e) Consider the sequence bn = (1 + 1
quence (2, ( 3
2 )2, ( 4
four decimal places, we obtain

n )n, n ∈ N. This is the se-
4 )4, . . .). If we approximate the values to

3 )3, ( 5

(2, 2.25, 2.3704, 2.4414, 2.4883, 2.5216, 2.5465, 2.5658, . . .).

Also b100 is approximately 2.7048 and b1,000 is approximately
2.7169.

The “limit” of a sequence (sn) is a real number that the values
sn are close to for large values of n. For instance, the values of the
sequence in Example 1(a) are close to 0 for large n and the values
of the sequence in Example 1(d) appear to be close to 1 for large n.

§7. Limits of Sequences 35

The sequence (an) given by an = (−1)n requires some thought. We
might say 1 is a limit because in fact an = 1 for the large values of n
that are even. On the other hand, an = −1 [which is quite a distance
from 1] for other large values of n. We need a precise deﬁnition in
order to decide whether 1 is a limit of an = (−1)n. It turns out that
our deﬁnition will require the values to be close to the limit value
for all large n, so 1 will not be a limit of the sequence an = (−1)n.

7.1 Deﬁnition.
A sequence (sn) of real numbers is said to converge to the real number
s provided that

for each (cid:3) > 0 there exists a number N such that

n > N implies

|sn − s| < (cid:3).

(1)

If (sn) converges to s, we will write limn→∞ sn = s, or sn → s. The
number s is called the limit of the sequence (sn). A sequence that
does not converge to some real number is said to diverge.

Several comments are in order. First, in view of the Archimedean
property, the number N in Deﬁnition 7.1 can be taken to be a positive
integer if we wish. Second, the symbol (cid:3) [lower case Greek epsilon]
in this deﬁnition represents a positive number, not some new exotic
number. However, it is traditional in mathematics to use (cid:3) and δ
[lower case Greek delta] in situations where the interesting or chal-
lenging values are the small positive values. Third, condition (1) is
an inﬁnite number of statements, one for each positive value of (cid:3).
The condition states that to each (cid:3) > 0 there corresponds a number
N with a certain property, namely n > N implies |sn − s| < (cid:3). The
value N depends on the value (cid:3), and normally N will have to be
large if (cid:3) is small. We illustrate these remarks in the next example.

Example 2
Consider the sequence sn = 3n+1
1
n and 4
lim sn = 3

n are very small for large n, it seems reasonable to conclude
7 . In fact, this reasoning will be completely valid after we

7n−4 . If we write sn as

3+ 1
n
7− 4
n

and note

36

2. Sequences

have the limit theorems in §9:

(cid:10)

(cid:11)

lim sn = lim

3 + 1
n
7 − 4
n

=

lim 3 + lim( 1
n )
lim 7 − 4 lim( 1
n )

=

3 + 0
7 − 4 · 0

=

3
7

.

However, for now we are interested in analyzing exactly what we
7 . By Deﬁnition 7.1, lim sn = 3
mean by lim sn = 3

7 means

for each (cid:3) > 0 there exists a number N such that

n > N implies

(1)

(cid:12)
(cid:12)
(cid:12) 3n+1
7n−4

− 3
7

(cid:12)
(cid:12)
(cid:12) < (cid:3).

As (cid:3) varies, N varies. In Example 2 of the next section we will show
that, for this particular sequence, N can be taken to be 19
49(cid:2) + 4
7 .
Using this observation, we ﬁnd that for (cid:3) equal to 1, 0.1, 0.01, 0.001,
and 0.000001, respectively, N can be taken to be approximately 0.96,
4.45, 39.35, 388.33, and 387,755.67, respectively. Since we are inter-
ested only in integer values of n, we may as well drop the fractional
part of N . Then we see ﬁve of the inﬁnitely many statements given
by (1) are:

n > 0

implies

n > 4

implies

n > 39 implies

n > 388 implies

n > 387,755 implies

(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)
(cid:12)

3n + 1
7n − 4
3n + 1
7n − 4
3n + 1
7n − 4
3n + 1
7n − 4
3n + 1
7n − 4

(cid:12)
(cid:12)
(cid:12)
(cid:12) < 1;
(cid:12)
(cid:12)
(cid:12)
(cid:12) < 0.1;
(cid:12)
(cid:12)
(cid:12)
(cid:12) < 0.01;
(cid:12)
(cid:12)
(cid:12)
(cid:12) < 0.001;
(cid:12)
(cid:12)
(cid:12)
(cid:12) < 0.000001.

− 3
7
− 3
7
− 3
7
− 3
7
− 3
7

(2)

(3)

(4)

(5)

(6)

Table 7.1 partially conﬁrms assertions (2) through (6). We could go
on and on with these numerical illustrations, but it should be clear
we need a more theoretical approach if we are going to prove results
about limits.

Example 3
We return to the examples in Example 1.

§7. Limits of Sequences 37

TABLE 7.1

sn = 3n+1
7n−4
is approximately

|sn − 3
7
is approximately

|

0.7000
0.5882
0.5417
0.5161
0.5000
0.4384
0.4295

0.2714
0.1597
0.1131
0.0876
0.0714
0.0098
0.0010

n

2
3
4
5
6
40
400

(a) lim 1

section.

n2 = 0. This will be proved in Example 1 of the next

(b) The sequence (an) where an = (−1)n does not converge. Thus
the expression “lim an” is meaningless in this case. We will
discuss this example again in Example 4 of the next section.

(c) The sequence cos( nπ
(d) The sequence n1/n appears to converge to 1. We will prove

3 ) does not converge. See Exercise 8.7.

lim n1/n = 1 in Theorem 9.7(c) on page 48.

(e) The sequence (bn) where bn = (1+ 1

n )n converges to the number
e that should be familiar from calculus. The limit lim bn and
the number e will be discussed further in Example 6 in §16 and
in §37. Recall e is approximately 2.7182818.

We conclude this section by showing that limits are unique. That
is, if lim sn = s and lim sn = t, then we must have s = t. In short,
the values sn cannot be getting arbitrarily close to diﬀerent values
for large n. To prove this, consider (cid:3) > 0. By the deﬁnition of limit
there exists N1 so that

n > N1

implies

|sn − s| <

and there exists N2 so that

n > N2

implies

|sn − t| <

(cid:3)
2

(cid:3)
2

.

For n > max{N1, N2}, the Triangle Inequality 3.7 shows
|s − t| = |(s − sn) + (sn − t)| ≤ |s − sn| + |sn − t| ≤ (cid:3)
2

+

(cid:3)
2

= (cid:3).

38

2. Sequences

This shows |s − t| < (cid:3) for all (cid:3) > 0. It follows that |s − t| = 0; hence
s = t.

Exercises

7.1 Write out the ﬁrst ﬁve terms of the following sequences.

(a) sn = 1
3n+1
(c) cn = n
3n

(b) bn = 3n+1
4n−1
(d) sin( nπ
4 )

7.2 For each sequence in Exercise 7.1, determine whether it converges. If

it converges, give its limit. No proofs are required.

7.3 For each sequence below, determine whether it converges and, if it

converges, give its limit. No proofs are required.
(b) bn = n2+3
(a) an = n
n2−3
n+1
(c) cn = 2−n
(d) tn = 1 + 2
n
(e) xn = 73 + (−1)n
(f ) sn = (2)1/n
(h) dn = (−1)nn
(g) yn = n!
(i) (−1)n
3
(j) 7n
+8n
2n3−3
(k) 9n2−18
(l) sin( nπ
2 )
6n+18
(n) sin( 2nπ
(m) sin(nπ)
3 )
n+1
+5
(p) 2
(o) 1
n sin n
2n−7
(q) 3n
(r) (1 + 1
n!
(s) 4n2+3
(t) 6n+4
9n2+7
3n2−2

n )2

n

7.4 Give examples of

(a) A sequence (xn) of irrational numbers having a limit lim xn

that is a rational number.

(b) A sequence (rn) of rational numbers having a limit lim rn that

is an irrational number.

7.5 Determine the following limits. No proofs are required, but show any

relevant algebra.

(a) lim sn where sn =

(b) lim(

n2 + n − n),

√

√

√

n2 + 1 − n,

(c) lim(

4n2 + n − 2n).
Hint for (a): First show sn =

1√

n2+1+n

.
