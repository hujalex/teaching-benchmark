|     | 76  |     |     |     |     |     | 7.GENERALROTATIONALMOTION* |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------------------------- | --- | --- |
δu
where isdefinedbyequation(7.3),andrepresentsthetimederivativeofu intherotatingbasis1. Wesee
δt
thatinadditiontothe‘regular’timederivative, actingonthecomponentsofu, wegetanadditionalterm
|     | ω×u |     |     | Notethatforu=ω,wefindthat |     |     | dω/dt =δω/δt | =ω˙,i.e.,thetime |     |
| --- | --- | --- | --- | ------------------------- | --- | --- | ------------ | ---------------- | --- |
duetotherotationofthesystem.
derivativeoftherotationvectoristhesameinthestationaryandrotatingframes.
Theprimeexampleofavectorisofcoursethepositionvectorr ofaparticle, thesecondderivativeof
whichappearsinNewton’ssecondlawofmotion.We’llcalculatethatsecondderivativeforapositionvector
inarotatingcoordinateframe.Thefirstderivativeisasimpleapplicationofequation(7.3):
|     |     |     |     |     | dr δr |     |     |     |     |
| --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
= +ω×r.
(7.4)
|     |     |     |     |     | dt δt |     |     |     |     |
| --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
Togetthesecondderivative,weapply(7.3)tothevelocityvectorfoundin(7.4):
|     |     |     |     | d2r d (cid:181)δr | (cid:182) |     |     |     |     |
| --- | --- | --- | --- | ----------------- | --------- | --- | --- | --- | --- |
|     |     |     |     | =                 | +ω×r      |     |     |     |     |
δt
|     |     |     |     | dt2 dt        |           |             |           |     |       |
| --- | --- | --- | --- | ------------- | --------- | ----------- | --------- | --- | ----- |
|     |     |     |     | δ (cid:181)δr | (cid:182) | (cid:181)δr | (cid:182) |     |       |
|     |     |     |     | =             | +ω×r +ω×  | +ω×r        |           |     |       |
|     |     |     |     | δt δt         |           | δt          |           |     |       |
|     |     |     |     | δ2r           | δω        | δr          |           |     |       |
|     |     |     |     | = +           | ×r+2ω×    | +ω×(ω×r).   |           |     | (7.5) |
|     |     |     |     | δt2           | δt        | δt          |           |     |       |
Likeinthetwo-dimensionalcasegivenbyequation(6.4),wefindthattheaccelerationinarotatingreference
frame picks up extra terms compared to a stationary (or more general, inertial) frame. To get a complete
picture,wealsoallowtheoriginoftherotatingframetobedifferentfromthatofthestationarylabframe.Let
r bethepositionvectorinthelabframe,Rthevectorpointingfromtheoriginofthelabframetothatofthe
lab
=R+r,andforthesecond
rotatingframe,andr thepositionvectorintherotatingframe.Wethenhaver lab
| 7   | derivativeofr | wefind: |     |     |     |     |     |     |     |
| --- | ------------- | ------- | --- | --- | --- | --- | --- | --- | --- |
lab
|     |     |     | d2r | d2r d2R        |     |       |     |     |       |
| --- | --- | --- | --- | -------------- | --- | ----- | --- | --- | ----- |
|     |     |     | lab | = +            |     |       |     |     |       |
|     |     |     | dt2 | dt2 dt2        |     |       |     |     |       |
|     |     |     |     | δ2r            |     | δr δω | d2R |     |       |
|     |     |     |     | = +ω×(ω×r)+2ω× |     | +     | ×r+ |     |       |
|     |     |     |     |                |     |       | .   |     | (7.6) |
|     |     |     |     | δt2            |     | δt δt | dt2 |     |       |
Wecansubstituteequation(7.6)inNewton’ssecondlawofmotioninthelabframe(i.e.,justF=dr
/dt)to
lab
findtheexpressionforthatlawintherotatingframe:
|     |     |     | δ2r | (cid:183)               |     |     | d2R (cid:184) |     |       |
| --- | --- | --- | --- | ----------------------- | --- | --- | ------------- | --- | ----- |
|     |     |     | m   | =F−m ω×(ω×r)+2ω×v+ω˙×r+ |     |     | ,             |     | (7.7) |
|     |     |     | δt2 |                         |     |     | dt2           |     |       |
wherewedefinedv=δr/δtasthevelocityintherotatingframe,andusedthatthetimederivativeofωisthe
sameinboththestationaryandtherotatingframe.Wefindthatwegetfourcorrectiontermstotheforcedue
toourtransitiontoarotatingframe.Theyarenot‘real’forceslikegravityorfriction,astheyvanishinthelab
frame,butyoucaneasilyexperiencetheireffects,whenyou’reinaturningcarorrotatingcarousel. Asthey
havenophysicalorigin,wecalltheseforcesfictitious.Theyareknownasthecentrifugal,Coriolis,azimuthal,
andtranslationalforce,respectively:
=−mω×(ω×r)
|     |     |     |     |     | F cf |     |     |     | (7.8) |
| --- | --- | --- | --- | --- | ---- | --- | --- | --- | ----- |
=−2mω×v
|     |     |     |     | F   | Cor |     |     |     | (7.9) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- |
=−mω˙×r
|     |     |     |     |     | F az |     |     |     | (7.10) |
| --- | --- | --- | --- | --- | ---- | --- | --- | --- | ------ |
d2R
|     |     |     |     | F   | =−m       |     |     |     | (7.11) |
| --- | --- | --- | --- | --- | --------- | --- | --- | --- | ------ |
|     |     |     |     |     | trans dt2 |     |     |     |        |
Weencounteredthecentrifugal, Coriolisandazimuthalforcebeforeinsection6.2. Toseehowtheex-
pressionsaboveconnecttotheplanarversions,letuspickthecoordinatesoftherotatingframesuchthatthe
directionofωcoincideswiththez-axis.Therotationalmotionandtheforcescanthenbedescribedinterms
ofthecylindricalcoordinatesconsistingofthepolarcoordinates(ρ,θ)inthexy-planeandzalongthez-axis
|     | (notethatweuseρ=(cid:112)  |     | x2+y2               |                             |     |                     |     |                  |     |
| --- | -------------------------- | --- | ------------------- | --------------------------- | --- | ------------------- | --- | ---------------- | --- |
|     |                            |     |                     | fortheradialdistanceinthexy |     | planeinsteadofr,asr |     | isnowthedistance |     |
|     |                            |     | (cid:179) (cid:180) | δ                           |     |                     |     |                  |     |
|     | 1Someauthorsusethenotation |     | d u                 | for u .                     |     |                     |     |                  |     |
d t rot δ t
