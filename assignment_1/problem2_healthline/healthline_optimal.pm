// HealthLine DTMC induced by the LP-optimal policy (Problem 2, Q2.c)
// Run:  prism healthline_optimal.pm healthline_optimal.props
dtmc

module healthline_dtmc
    s : [0..11] init 0;
    [classify] s=0 -> 0.25 : (s'=1) + 0.45 : (s'=2) + 0.20 : (s'=3) + 0.10 : (s'=11);
    [thorough_screen] s=1 -> 0.25 : (s'=4) + 0.50 : (s'=5) + 0.25 : (s'=11);
    [detailed_response] s=2 -> 0.85 : (s'=6) + 0.15 : (s'=11);
    [auto_process] s=3 -> 0.60 : (s'=7) + 0.25 : (s'=9) + 0.15 : (s'=11);
    [emergency_referral] s=4 -> 1.00 : (s'=10);
    [offer_nurse] s=5 -> 1.00 : (s'=8);
    [check_satisfaction] s=6 -> 0.55 : (s'=7) + 0.35 : (s'=8) + 0.10 : (s'=11);
    [done] s>=7 -> true;
endmodule

label "initial" = (s=0);
label "acute_track" = (s=1);
label "general_track" = (s=2);
label "admin_track" = (s=3);
label "warning_signs" = (s=4);
label "no_warning_signs" = (s=5);
label "information_delivered" = (s=6);
label "resolved" = (s=7);
label "escalated_nurse" = (s=8);
label "escalated_admin" = (s=9);
label "emergency" = (s=10);
label "abandoned" = (s=11);
label "terminal" = (s>=7);

rewards "outcome"
    s=7 : 10;
    s=8 : 6;
    s=9 : 5;
    s=10 : 12;
    s=11 : 0;
endrewards
