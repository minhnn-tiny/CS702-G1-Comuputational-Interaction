// HealthLine triage assistant -- Markov decision process (Problem 2, Q1.b)
// Build / syntax check:   prism healthline.pm
// Verify properties:      prism healthline.pm healthline.props
mdp

module healthline
    // Define states here!
    // One integer variable encodes the twelve states s_0 ... s_11:
    //   0  initial               : patient describes concern
    //   1  acute_track           : awaiting triage
    //   2  general_track         : awaiting information delivery
    //   3  admin_track           : awaiting request processing
    //   4  triage_complete       : warning signs detected
    //   5  triage_complete       : no warning signs
    //   6  information_delivered : patient assessing
    //   7  resolved              : resolved without escalation      (terminal)
    //   8  escalated_nurse       : escalated to nurse               (terminal)
    //   9  escalated_admin       : escalated to admin staff         (terminal)
    //  10  emergency             : emergency referral               (terminal)
    //  11  abandoned             : patient abandoned                (terminal)
    s : [0..11] init 0;

    // Define actions and transition probabilities here!
    [classify]           s=0 -> 0.25 : (s'=1) + 0.45 : (s'=2) + 0.20 : (s'=3) + 0.10 : (s'=11);

    [quick_screen]       s=1 -> 0.15 : (s'=4) + 0.65 : (s'=5) + 0.20 : (s'=11);
    [thorough_screen]    s=1 -> 0.25 : (s'=4) + 0.50 : (s'=5) + 0.25 : (s'=11);

    [brief_response]     s=2 -> 0.75 : (s'=6) + 0.25 : (s'=11);
    [detailed_response]  s=2 -> 0.85 : (s'=6) + 0.15 : (s'=11);

    [auto_process]       s=3 -> 0.60 : (s'=7) + 0.25 : (s'=9) + 0.15 : (s'=11);
    [transfer_to_admin]  s=3 -> 0.90 : (s'=9) + 0.10 : (s'=11);

    [emergency_referral] s=4 -> 1.00 : (s'=10);
    [offer_nurse]        s=4 -> 0.85 : (s'=8) + 0.15 : (s'=10);

    [offer_nurse]        s=5 -> 1.00 : (s'=8);

    [check_satisfaction] s=6 -> 0.55 : (s'=7) + 0.35 : (s'=8) + 0.10 : (s'=11);

    // Terminal states 7-11 are absorbing (self-loop, no further choice)
    [done]               s>=7 -> true;
endmodule

// Labels
// Use labels to name the states
label "initial"               = (s=0);
label "acute_track"           = (s=1);
label "general_track"         = (s=2);
label "admin_track"           = (s=3);
label "triage_complete"       = (s=4 | s=5);
label "warning_signs"         = (s=4);
label "no_warning_signs"      = (s=5);
label "information_delivered" = (s=6);
label "resolved"              = (s=7);
label "escalated_nurse"       = (s=8);
label "escalated_admin"       = (s=9);
label "emergency"             = (s=10);
label "abandoned"             = (s=11);
label "terminal"              = (s>=7);

rewards "outcome"
    // Define rewards here!
    // Terminal-state rewards (state rewards; the reward is obtained on reaching the state)
    s=7  : 10;   // resolved         -- efficient resolution
    s=8  : 6;    // escalated_nurse  -- appropriate care, higher cost
    s=9  : 5;    // escalated_admin  -- request handled
    s=10 : 12;   // emergency        -- critical safety outcome
    s=11 : 0;    // abandoned        -- poor experience
endrewards
