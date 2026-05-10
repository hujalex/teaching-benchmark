| 4.5. EXTRAPOLATION |     |     |     |     |     |     |     |     |     |     |     | 175 |
| ------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Sadly, this sequence of approximations is not converging very quickly. We have two digits of accuracy in the first
approximationandstillonlythreedigitsofaccuracyinthefifth. Wecould,ofcourse,continuetomakehsmallerto
getmoreaccurateapproximations,butbasedontheslowimprovementobservedsofar,thisdoesnotseemlikeavery
promising route. Instead, we can combine the estimates we already have to get an improved approximation. This
idea should remind you, at least on the surface, of Aitken’s delta-squared method. In that method, we combined
threeconsecutiveapproximationstoformanotherthatwasgenerallyabetterapproximationthananyoftheoriginal
three. We will do something similar here, combining inadequate approximations to find better ones. We will name
| the various | new | approximations |                         | for                   | continued | reuse. |     |                               |     |     |     |     |
| ----------- | --- | -------------- | ----------------------- | --------------------- | --------- | ------ | --- | ----------------------------- | --- | --- | --- | --- |
|             |     |                |                         | 2e˜(0.005)−e˜(0.01)   |           |        | ≡   | e˜1(0.01)=2.718220416437056   |     |     |     |     |
|             |     |                |                         | 2e˜(0.0025)−e˜(0.005) |           |        | ≡   | e˜1(0.005)=2.718266365833184  |     |     |     |     |
|             |     |                | 2e˜(0.00125)−e˜(0.0025) |                       |           |        | ≡   | e˜1(0.0025)=2.718277948983707 |     |     |     |     |
2e˜(0.000625)−e˜(0.00125) ≡ e˜1(0.00125)=2.718280856855920. (4.5.1)
Each of these new approximations is accurate to 5 or 6 significant digits! Already a significant improvement. We
| can combine | them | further | to  | find yet | better | approximations: |     |     |     |     |     |     |
| ----------- | ---- | ------- | --- | -------- | ------ | --------------- | --- | --- | --- | --- | --- | --- |
4e˜1(0.005)−e˜1(0.01)
|     |     |     |     |     |     |     | ≡   | e˜2(0.01)=2.718281682298560 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------- | --- | --- | --- | --- |
3
4e˜1(0.0025)−e˜1(0.005)
|     |     |     |     |     |     |     | ≡   | e˜2(0.005)=2.718281810033881 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------- | --- | --- | --- | --- |
3
4e˜1(0.00125)−e˜(0.0025)
|     |     |     |     |     |     |     | ≡   | e˜2(0.0025)=2.718281826146657. |     |     |     | (4.5.2) |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------ | --- | --- | --- | ------- |
3
The first of these approximations is accurate to seven significant digits, the second to eight, and the third to nine!
| And we | can combine |     | them further: |     |     |     |     |     |     |     |     |     |
| ------ | ----------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
8e˜2(0.005)−e˜2(0.01)
|     |     |     |     |     |     |     | ≡   | e˜3(0.01)=2.718281828281785 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------- | --- | --- | --- | --- |
7
8e˜2(0.0025)−e˜2(0.005)
|     |     |     |     |     |     |     | ≡   | e˜3(0.005)=2.718281828448482. |     |     |     | (4.5.3) |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | ------- |
7
Nowwehaveapproximationsaccuratetotenandelevensignificantdigits! Lookingback,wetookfiveapproximations
that had no better than 3 significant digits of accuracy and combined them to get two approximations that were
accurate to at least 10 significant digits each. Magic! Okay, not magic, mathemagic! Here is how it works.
| Suppose | we  | are approximating |     |                | p using | the formula | p˜(h),  | and | we know | that   |     |     |
| ------- | --- | ----------------- | --- | -------------- | ------- | ----------- | ------- | --- | ------- | ------ | --- | --- |
|         |     |                   |     | p˜(h)=p+c1·hm1 |         |             | +c2·hm2 |     | +c3·hm3 |        |     |     |
|         |     |                   |     |                |         |             |         |     |         | +··· . |     |     |
Then
p˜(αh)=p+c1·(αh)m1
|     |     |     |     |     |     |     | +c2·(αh)m2 |     | +c3·(αh)m3 | +··· | .   |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | --- | ---------- | ---- | --- | --- |
Now, if we multiply the second equation by α−m1 and subtract the first from it, the hm1 terms vanish, and we get
| an approximation |     | with       | error   | term | beginning    | with | c2·hm2:   |         |      |           |      |     |
| ---------------- | --- | ---------- | ------- | ---- | ------------ | ---- | --------- | ------- | ---- | --------- | ---- | --- |
|                  |     | α−m1p˜(αh) |         |      | α−m1p+c1·hm1 |      | +c2αm2−m1 |         | ·hm2 | +c3αm3−m1 | ·hm3 |     |
|                  |     |            |         | =    |              |      |           |         |      |           | +··· |     |
|                  |     |            | −[p˜(h) | =    | p+c1·hm1     |      | +c2·hm2   | +c3·hm3 |      | +···]     |      |     |
α−m1p˜(αh)−p˜(h) = (α−m−1)p+c2(αm2−m1 −1)·hm2 +c3(αm3−m1 −1)·hm3 +···
| With a | little rearranging, |     |     |     |     |     |     |     |     |     |     |     |
| ------ | ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
α−m1p˜(αh)−p˜(h)
|     |     |     |     |     |      |     | =p+d2·hm2 |     | +d3·hm3 | +··· |     | (4.5.4) |
| --- | --- | --- | --- | --- | ---- | --- | --------- | --- | ------- | ---- | --- | ------- |
|     |     |     |     |     | α−m1 | −1  |           |     |         |      |     |         |
for some constants d2,d3,.... If m2 >m1, then this method will tend to improve on the two approximations p˜(h)
and p˜(αh) by combining them into a single approximation with error commensurate with some constant multiple
| of hm2. | This calculation |     | is the    | basis   | for Richardson’s |      | extrapolation. |      |      |        |     |         |
| ------- | ---------------- | --- | --------- | ------- | ---------------- | ---- | -------------- | ---- | ---- | ------ | --- | ------- |
| It just | so happens       |     | e˜(h) has | exactly | the              | form | needed.        |      |      |        |     |         |
|         |                  |     |           |         |                  |      | 2              |      | 3 4  | 5      |     |         |
|         |                  |     |           |         | e˜(h)=e+c1h+c2h  |      |                | +c3h | +c4h | +O(h ) |     | (4.5.5) |
