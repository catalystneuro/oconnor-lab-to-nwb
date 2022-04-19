tg_units = dict(
    MOI="kg m2",
    barCoor="pixel",
    barRadii="pixel",
    barAzim="degree",
    position="degree",
    velocity="degree/s",
    acceleration="degree/s^2",
    jerk="degree/s^3",
    phase="radians",
    amplitude="degree",
    setpoint="degree",
    frequency="Hz",
    thetaAtContact="degree",
    distanceToPole="mm",
    contact="boolean",
    follicleCoordsX="mm",
    follicleCoordsY="mm",
    deltaKappa="1/mm",
    Fnorm="N",
    Faxial="N",
    Flateral="N",
    M0="N*m",
    Mi="N*m",
    dFaxial="N/s",
    dFlateral="N/s",
    dM0="N*m/s",
    dMi="N*m/s",
)

crossmodal_units = dict(
    somStim="volt",
    visStim="volt",
    lLick="volt",
    rLick="volt",
    vTube="volt",
    hTube="volt",
    opto1="volt",
    opto2="volt"
)

seqlick_units = dict(
    cue="ms",
    posIndex="Null",
    water="ms",
    opto="Null",
    noLickITI="ms",
    is_tongue_out="Null",
    prob_tongue_out="%",
    tongue_bottom_lm="pixels"
)

seqlick_dirs = [
    "Data behav air",
    "Data behav earplug",
    "Data behav numbing",
    "Data ephys ALM",
    "Data ephys M1B",
    "Data ephys M1TJ",
    "Data ephys others",
    "Data ephys S1BF",
    "Data ephys S1L",
    "Data ephys S1TJ",
    "Data ephys ZZ",
    "Data learning",
    "Data opto VGAT-CRE Ai32 2s 2.5V",
    "Data opto VGAT-CRE Ai32 2s 5V",
    "Data opto VGAT-CRE Ai32 efficiency"
]