|        |                          |                  |         |        |            |     |     | stochastic | inventory          | control      | 135  |
| ------ | ------------------------ | ---------------- | ------- | ------ | ---------- | --- | --- | ---------- | ------------------ | ------------ | ---- |
|        |                          |                  |         |        |            |     |     |            | # Optimal policy:  | (6,40)       |      |
| import | numpy                    | as np, functools |         |        |            |     |     |            |                    |              |      |
| from   | scipy.stats              | import           | poisson |        |            |     |     |            | # c(s*,S*) = 35.02 |              |      |
| from   | inventoryanalytics.utils |                  |         | import | memoize as | mem |     |            |                    |              |      |
|        |                          |                  |         |        |            |     |     |            | instance = {’mu’:  | 10, ’K’: 64, | ’h’: |
def expectation(f, x, p): # E[f(X)] = sum f(x_i) p_i 1., ’b’: 9.}
pb = ZhengFedergruen(**instance)
return np.dot(f(x),p)
print(pb.findOptimalPolicy())
class ZhengFedergruen(object):
| """ |     |     |     |     |     |     |     |     | Listing73 |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- | --- | --- |
Aninstanceofthestation-
| The | stationary | stochastic |     | lot sizing | problem. |     |     |     |     |     |     |
| --- | ---------- | ---------- | --- | ---------- | -------- | --- | --- | --- | --- | --- | --- |
arystochasticlotsizingproblem.The
"""
def __init__(self, mu, K, h, b): executionpathisillustratedinFig.
101.
"""
|     | Constructs | an instance |     | of the stochastic |     | lot sizing | problem |     |     |     |     |
| --- | ---------- | ----------- | --- | ----------------- | --- | ---------- | ------- | --- | --- | --- | --- |
Arguments:
|     | mu         | {[type]} -- | the expected     |          | demand  |      |     |     |     |     |     |
| --- | ---------- | ----------- | ---------------- | -------- | ------- | ---- | --- | --- | --- | --- | --- |
|     | K {[type]} | --          | the fixed        | ordering | cost    |      |     |     |     |     |     |
|     | h {[type]} | --          | the proportional |          | holding | cost |     |     |     |     |     |
|     | b {[type]} | --          | the penalty      | cost     |         |      |     |     |     |     |     |
"""
|     | self.K,   | self.h,                         | self.b,        | self.mu    | = K, h,                  | b, mu    |                        |     |     |     |     |
| --- | --------- | ------------------------------- | -------------- | ---------- | ------------------------ | -------- | ---------------------- | --- | --- | --- | --- |
|     | self.p    | = poisson.pmf(np.arange(10*mu), |                |            | self.mu)                 | #        | set a safe upper bound | for | S   |     |     |
|     |           | the random                      | variable       | support    | (e.g.                    | 10 times | the mean demand)       |     |     |     |     |
| def | G_L(self, | y): #                           | the one-period |            | inventory                | cost     |                        |     |     |     |     |
|     | return    | self.b*np.maximum(0,-y)         |                |            | + self.h*np.maximum(0,y) |          |                        |     |     |     |     |
| def | G(self,   | y): # expected                  |                | one period | inventory                | cost     |                        |     |     | s   |     |
expectation(self.G_L,
return y - np.arange(0, len(self.p)), self.p) Fig.101 Executionofthealgorithmfor
theinstanceinListing73.
| @memoize |         | # see appendix              | on           | SDP for     | memoize   | class implementation |     |     |     |     |     |
| -------- | ------- | --------------------------- | ------------ | ----------- | --------- | -------------------- | --- | --- | --- | --- | --- |
| def      | m(self, | j): # [Zheng                | and          | Federgruen, | 1991]     | eq. 2a               |     |     |     |     |     |
|          | if j == | 0:                          |              |             |           |                      |     |     |     |     |     |
|          | return  | 1./(1.                      | - self.p[0]) |             |           |                      |     |     |     |     |     |
|          | else:   | # [Zheng and                | Federgruen,  |             | 1991] eq. | 2b                   |     |     |     |     |     |
|          | res     | = sum(self.p[l]*self.m(j-l) |              |             | for l     | in range(1,j+1))     |     |     |     |     |     |
|          | res     | /= (1. -                    | self.p[0])   |             |           |                      |     |     |     |     |     |
|          | return  | res                         |              |             |           |                      |     |     |     |     |     |
@memoize
| def | M(self, | j): # [Zheng | and | Federgruen, | 1991] | eq. 2c |     |     |     |     |     |
| --- | ------- | ------------ | --- | ----------- | ----- | ------ | --- | --- | --- | --- | --- |
|     | if j == | 0:           |     |             |       |        |     |     |     |     |     |
|     | return  | 0.           |     |             |       |        |     |     |     |     |     |
else:
|     | return  | self.M(j-1)               | +      | self.m(j-1)     |          |             |     |     |                              |     |     |
| --- | ------- | ------------------------- | ------ | --------------- | -------- | ----------- | --- | --- | ---------------------------- | --- | --- |
| def | k(self, | s,y): #                   | [Zheng | and Federgruen, |          | 1991] eq.   | 5   |     |                              |     |     |
|     | res =   | self.K                    |        |                 |          |             |     |     |                              |     |     |
|     | res +=  | sum(self.m(j)*self.G(y-j) |        |                 | for j in | range(y-s)) |     |     |                              |     |     |
|     | return  | res                       |        |                 |          |             |     |     | findOptimalPolicy:Weenterthe |     |     |
algorithmwithaninitial(arbitrary)
def c(self, s,S): # [Zheng and Federgruen, 1991] eq. 3 order-up-to-levelS0 = y∗,where
return self.k(s,S)/self.M(S-s) y∗ (cid:44) minyG(y).Wefindanoptimal
correspondingreorderlevels0by
decreasingsfromy∗withunit-sized
def findOptimalPolicy(self):
|     |     |     |     |     |     |     |     |     | decrementsuntilc(s,S0) | <=  | G(s). |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------------------- | --- | ----- |
# [Zheng and Federgruen, 1991] algorithm on Page 659 Optimalityofs0forS0followsfrom
|     | ystar | = poisson.ppf(self.b/(self.b+self.h),self.mu).astype(int) |     |     |     |     | #base | stock |     |     |     |
| --- | ----- | --------------------------------------------------------- | --- | --- | --- | --- | ----- | ----- | --- | --- | --- |
Corollary2.Wethensearchforthe
|     |     | level, an | arbitrary | minimum | of G |     |     |     |     |     |     |
| --- | --- | --------- | --------- | ------- | ---- | --- | --- | --- | --- | --- | --- |
s = ystar - 1 # upper bound for s* smallestvalueofSthatislarger
S_0 = ystar + 0 # lower bound for S* thanS0andimprovesuponS0.Sis
#calculate the optimal s for S_0 by decreasing s until c(s,S_0) <= G(s) increasedwithunit-sizedincrements.
Asinglecomparisonofc(s0,S)and
|     | while | self.c(s,S_0) | > self.G(s): |     |     |     |     |     |     |     |     |
| --- | ----- | ------------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
c(s0,S0)issufficienttoverifyifa
|     | s -= | 1   |     |     |     |     |     |     |     |     |     |
| --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
s_0 = s # optimal value of s for S_0 givenvalueofSimprovesuponS0
|     |     | _   | S_  |     |     |     |     | (s_0,S_0) |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------- | --- | --- | --- |
c 0 = s el f. c( s 0, 0) # e x pe c t e d long run average cost per period of (Lemma53).IfSimprovesupon
|     | S 0 = S | _ 0 # S 0 = | S ^0 of | t h e p a p e | r   |     |     |     |     |     |     |
| --- | ------- | ----------- | ------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
S0,S0isupdatedtoSandthenew
|     | S = S0 | + 1       |        |     |     |     |     |     |                                  |     |     |
| --- | ------ | --------- | ------ | --- | --- | --- | --- | --- | -------------------------------- | --- | --- |
|     | while  | self.G(S) | <= c0: |     |     |     |     |     | correspondingoptimalreorderlevel |     |     |
if self.c(s,S) < c0: # S improves upon S0 s0isdeterminedbyincrementing
S0 = S
while self.c(s,S0) <= self.G(s+1): # calculate the optimal s for S_0 theoldreorderlevelwithunit-sized
|     |     |     |     |     |     |     |     |     | incrementsuntilc(s,S0) | > G(s+1). |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------------------- | --------- | --- |
s += 1
c0 = self.c(s,S0)
Theexistenceofsuchareorderlevel
|     | S += | 1   |     |     |     |     |     |     | s0,itsoptimalityforthenewvalue |     |     |
| --- | ---- | --- | --- | --- | --- | --- | --- | --- | ------------------------------ | --- | --- |
_
|     | s e l f . s | s t a r = s    |     |     |     |     |     |     | S0,andthefactthats0 | < y∗,areall |     |
| --- | ----------- | -------------- | --- | --- | --- | --- | --- | --- | ------------------- | ----------- | --- |
|     | s e l f . S | _ s t a r = S0 |     |     |     |     |     |     |                     |             |     |
guaranteedbyLemma54.
|     | return | s, S0 |     |     |     |     |     |     |     |     |     |
| --- | ------ | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
