#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "simulator.h"

struct atomtype element[]={
    {0.001,  1.0,  0.130, 1, "LP"},  /*  0 Lone Pair */
    {1.674, 0.79,  0.382, 1, "H"},   /*  1 Hydrogen */
    {6.646,  1.4,  0.666, 0, "He"},  /*  2 Helium */
    {11.525, 4.0,  0.666, 1, "Li"},  /*  3 Lithium */
    {14.964, 3.0,  0.666, 2, "Be"},  /*  4 Beryllium */
    {17.949, 2.0,  0.666, 3, "B"},   /*  5 Boron */
    {19.925, 1.84, 0.357, 4, "C"},   /*  6 Carbon */
    {23.257, 1.55, 0.447, 3, "N"},   /*  7 Nitrogen */
    {26.565, 1.74, 0.406, 2, "O"},   /*  8 Oxygen */
    {31.545, 1.65, 0.634, 1, "F"},   /*  9 Fluorine */
    {33.49,  1.82, 0.666, 0, "Ne"},  /* 10 Neon */
    {38.173, 4.0,  1.666, 1, "Na"},  /* 11 Sodium */
    {40.356, 3.0,  1.666, 2, "Mg"},  /* 12 Magnesium */
    {44.800, 2.5,  1.666, 3, "Al"},  /* 13 Aluminum */
    {46.624, 2.25, 1.137, 4, "Si"},  /* 14 Silicon */
    {51.429, 2.11, 1.365, 3, "P"},   /* 15 Phosphorus */
    {53.233, 2.11, 1.641, 2, "S"},   /* 16 Sulfur */
    {58.867, 2.03, 1.950, 1, "Cl"},  /* 17 Chlorine */
    {66.33,  1.88, 1.666, 0, "Ar"},  /* 18 Argon */
    {64.926, 5.0,  2.666, 1, "K"},   /* 19 Potassium */
    {66.549, 4.0,  2.666, 2, "Ca"},  /* 20 Calcium */
    {74.646, 3.7,  2.666, 3, "Sc"},  /* 21 Scandium */
    {79.534, 3.5,  2.666, 4, "Ti"},  /* 22 Titanium */
    {84.584, 3.3,  2.666, 5, "V"},   /* 23 Vanadium */
    {86.335, 3.1,  2.666, 6, "Cr"},  /* 24 Chromium */
    {91.22,  3.0,  2.666, 7, "Mn"},  /* 25 Manganese */
    {92.729, 3.0,  2.666, 3, "Fe"},  /* 26 Iron */
    {97.854, 3.0,  2.666, 3, "Co"},  /* 27 Cobalt */
    {97.483, 3.0,  2.666, 3, "Ni"},  /* 28 Nickel */
    {105.513, 3.0, 2.666, 2, "Cu"},  /* 29 Copper */
    {108.541, 2.9, 2.666, 2, "Zn"},  /* 30 Zinc */
    {115.764, 2.7, 2.666, 3, "Ga"},  /* 31 Gallium */
    {120.53,  2.5, 2.666, 4, "Ge"},  /* 32 Germanium */
    {124.401, 2.2, 2.666, 5, "As"},  /* 33 Arsenic */
    {131.106, 2.1, 2.666, 6, "Se"},  /* 34 Selenium */
    {132.674, 2.0, 2.599, 1, "Br"},  /* 35 Bromine */
    {134.429, 1.9, 2.666, 0, "Kr"}   /* 36 Krypton */
};

const int NUMELTS = sizeof(element) / sizeof(struct atomtype);

/* NB! all the Evdw that end in .666 are unknown */


struct bsdata bstab[]={
    // order,atom1,atom2   springConstant  nominalDist, de, beta*0.01
    bondrec(1,1,6,  460.0, 111.3, 0.671, 1.851),	/* H-C */
    bondrec(1,1,7,  460.0, 102.3, 0.721, 1.851),	/* H-N XXX */
    bondrec(1,1,8,  460.0,  94.2, 0.753, 1.747),	/* H-O */
    bondrec(1,1,14, 360.0, 125.6, 0.753, 1.747),	/* H-Si XXX */
    bondrec(1,1,16, 360.0, 125.2, 0.753, 1.747),	/* H-S XXX */
    bondrec(1,6,6,  440.0, 152.3, 0.556, 1.989),	/* C-C */
    bondrec(1,6,7,  510.0, 143.8, 0.509, 2.238),	/* C-N */
    bondrec(1,6,8,  536.0, 140.2, 0.575, 2.159),	/* C-O */
    bondrec(1,6,9,  510.0, 139.2, 0.887, 1.695),	/* C-F */
    bondrec(1,6,14, 297.0, 188.0, 0.624, 1.543),	/* C-Si */
    bondrec(1,6,15, 291.0, 185.6, 0.624, 1.543),	/* C-P XXX */
    bondrec(1,6,16, 321.3, 181.5, 0.539, 1.726),	/* C-S */
    bondrec(1,6,17, 323.0, 179.5, 0.591, 1.653),	/* C-Cl */
    bondrec(1,6,35, 230.0, 194.9, 0.488, 1.536),	/* C-Br */
    bondrec(1,7,7,  560.0, 138.1, 0.417, 2.592),	/* N-N */
    bondrec(1,7,8,  670.0, 142.0, 0.350, 3.200),	/* N-O XXX */
    bondrec(1,8,8,  781.0, 147.0, 0.272, 3.789),	/* O-O */
    bondrec(1,14,14,185.0, 233.2, 0.559, 1.286),	/* Si-Si */
    bondrec(1,14,16,185.0, 233.2, 0.559, 1.286),	/* Si-S  XXX */
    /* double bonds */
    bondrec(2,6,6,  960.0, 133.7, 1.207, 1.994),	/* C=C */
    bondrec(2,6,8, 1080.0, 120.8, 1.300, 2.160),	/* C=O XXX */
    bondrec(2,6,16, 321.3, 171.5, 1.150, 1.750),	/* C=S */
    /* triple bonds */
    bondrec(3,6,6, 1560.0, 121.2, 1.614, 2.198),	/* C~C */
    /* aromatic bonds */
    bondrec(4,1,6,  465.0, 108.3, 0.700, 1.850),	/* H-C XXX */
    bondrec(4,6,6,  660.0, 142.1, 0.800, 2.000),	/* C-C XXX */
    bondrec(4,6,7,  515.0, 135.2, 0.530, 2.250),	/* C-N XXX */
    bondrec(4,6,8,  536.0, 136.2, 0.900, 2.160),	/* C-O XXX */
    bondrec(4,6,9,  510.0, 139.2, 0.900, 1.700),	/* C-F XXX */
    bondrec(4,6,16, 321.3, 173.5, 0.800, 1.750),	/* C-S XXX */
	
    /* Next are some kludges Will put in just to make the
     * fine motion controller work. Numbers are guaranteed
     * to be bogus.
     */
    bondrec(1,8,14, 0.3, 173.5, 0.0, 0.50),	/* O-Si XXX */
    bondrec(1,7,14, 0.3, 173.5, 0.0, 0.50),	/* N-Si XXX */
    bondrec(1,7,16, 0.3, 173.5, 0.0, 0.50),	/* N-S  XXX */
};

/* NB -- XXX means De and beta are guesses */

const int BSTABSIZE = sizeof(bstab) / sizeof(struct bsdata);

struct angben bendata[]={
    // atom,order,atom,order,atom,  angularSpringConstant,  radians
    benrec(6,1,6,1,6, 450, 1.911),	/* C-C-C */
    benrec(6,1,6,1,1, 360, 1.909),	/* C-C-H */
    benrec(1,1,6,1,1, 320, 1.909),	/* H-C-H */
    benrec(6,1,6,1,9, 650, 1.911),	/* C-C-F */
    benrec(9,1,6,1,9, 1070, 1.869),	/* F-C-F */
    // benrec(6,4,6,4,6, 450, 2.046),	/* C-Csp2-C   4?? */
    benrec(6,2,6,2,6, 450, 2.046),	/* C-Csp2-C */
    benrec(6,1,6,2,6, 550, 2.119),	/* C-C=C */
    benrec(1,1,6,2,6, 360, 2.094),	/* C=C-H */
    benrec(6,1,6,3,6, 200, 3.142),	/* C-C-=C */
    benrec(6,1,6,2,8, 460, 2.138),	/* C-C=O */
    benrec(6,1,8,1,1, 770, 1.864),	/* C-O-H */
    benrec(6,1,8,1,6, 770, 1.864),	/* C-O-C */
    benrec(6,1,8,1,8, 770, 1.864),	/* C-O-O XXX */
    benrec(6,1,8,1,7, 770, 1.864),	/* C-O-N XXX */
    benrec(7,1,8,1,7, 770, 1.864),	/* N-O-N XXX */
    benrec(7,1,8,1,8, 770, 1.864),	/* N-O-O XXX */
    benrec(8,1,8,1,8, 770, 1.864),	/* O-O-O XXX */
    benrec(6,1,7,1,6, 630, 1.880),	/* C-N-C */
    benrec(6,1,7,1,7, 630, 1.880),	/* C-N-N XXX */
    benrec(6,1,7,1,8, 630, 1.880),	/* C-N-O XXX */
    benrec(7,1,7,1,7, 630, 1.880),	/* N-N-N XXX */
    benrec(6,1,6,1,8, 700, 1.876),	/* C-C-O */
    benrec(7,1,6,1,8, 630, 1.900),	/* N-C-O */
    benrec(7,1,7,1,8, 630, 1.900),	/* N-N-O XXX */
    benrec(8,1,7,1,8, 630, 1.900),	/* O-N-O XXX */
    benrec(7,1,6,1,16, 630, 1.900),	/* N-C-S XXX */
    benrec(6,1,6,1,7, 570, 1.911),	/* C-C-N */
    benrec(1,1,6,1,8, 600, 1.876),	/* H-C-O XXX */
    benrec(1,1,6,1,7, 470, 1.911),	/* H-C-N XXX */
    benrec(1,1,7,1,8, 600, 1.876),	/* H-N-O XXX */
    benrec(1,1,7,1,6, 470, 1.911),	/* H-N-C XXX */
    benrec(1,1,7,1,7, 470, 1.911),	/* H-N-N XXX */
    benrec(14,1,14,1,14, 350, 1.943),	/* Si-Si-Si */
    benrec(1,1,14,1,14, 350, 1.943),	/* H-Si-Si XXX */
    benrec(1,1,14,1,16, 350, 1.943),	/* H-Si-S XXX */
    benrec(16,1,14,1,16, 350, 1.943),	/* S-Si-S XXX */
    benrec(16,1,14,1,14, 350, 1.943),	/* S-Si-Si XXX */
    benrec(14,1,6,1,14, 400, 2.016),	/* Si-C-Si */
    benrec(6,1,14,1,6, 480, 1.934),	/* C-Si-C */
    benrec(17,1,6,1,17, 1080, 1.950),	/* Cl-C-Cl */
    benrec(6,1,6,1,16, 550, 1.902),	/* C-C-S */
    benrec(6,1,16,1,6, 720, 1.902),	/* C-S-C */
    benrec(14,1,16,1,14, 720, 1.902),	/* Si-S-Si XXX */
	
    /* Next are some kludges Will put in just to make the
     * fine motion controller work. Numbers guaranteed wrong.
     */
    benrec(7,1,16,1,6, 0, 1.902),
    benrec(6,1,8,1,14, 0, 1.902),
    benrec(8,1,14,1,6, 0, 1.902),
    benrec(8,1,14,1,1, 0, 1.902),
    benrec(6,1,14,1,1, 0, 1.902),
    benrec(8,1,14,1,8, 0, 1.902),
    benrec(9,1,6,1,7, 0, 1.902),
    benrec(7,1,14,1,8, 0, 1.902),
    benrec(6,1,16,1,14, 0, 1.902),
    benrec(16,1,14,1,8, 0, 1.902),
    benrec(16,1,14,1,7, 0, 1.902),
    benrec(14,1,7,1,14, 0, 1.902),
    benrec(14,1,7,1,6, 0, 1.902),
    benrec(7,1,14,1,7, 0, 1.902),
    benrec(8,1,6,1,16, 0, 1.902),
    benrec(1,1,6,1,16, 0, 1.902),
    benrec(6,1,6,1,14, 0, 1.902),
    benrec(16,1,6,1,14, 0, 1.902),
    benrec(8,1,6,1,9, 0, 1.902),
    benrec(7,1,16,1,7, 0, 1.902),
    benrec(16,1,7,1,16, 0, 1.902),
    benrec(16,1,7,1,14, 0, 1.902),
    benrec(14,1,8,1,7, 0, 1.902),
    benrec(1,1,14,1,7, 0, 1.902),
    benrec(14,1,14,1,7, 0, 1.902),
    benrec(14,1,14,1,6, 0, 1.902),
    benrec(7,1,14,1,6, 0, 1.902),
    benrec(14,1,6,1,1, 0, 1.902),
    benrec(14,1,14,1,8, 0, 1.902),
    benrec(14,1,6,1,8, 0, 1.902),
    benrec(14,1,6,1,7, 0, 1.902),
};

const int BENDATASIZE = sizeof(bendata) / sizeof(struct angben);

/*
 * Local Variables:
 * c-basic-offset: 4
 * tab-width: 8
 * End:
 */
