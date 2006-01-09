
struct configuration 
{
  // Value of the function at this configuration, the "potential
  // energy".  Only valid if functionValueValid is non-zero.  Call
  // evaluate() to generate and return this value.
  double functionValue;

  // The position of this configuration in N-dimensional space.  These
  // are the values that we're changing as we search for the minimum
  // functionValue.  Always valid.
  double *coordinate;

  // N-dimensional vector pointing downhill from this configuration.
  // May be NULL if the gradient hasn't been evaluated here.
  double *gradient;

  // Largest absolute value across all of the coordinates in the above
  // gradient.  Used to scale parameter values in tolerance
  // calculations, so our tolerances are based on the largest
  // coordinate motion along the gradient, not on the parameter
  // variation.
  double maximumCoordinateInGradient;

  // If this configuration was generated by a linear extrapolation
  // along the gradient of another configuration, then parameter is
  // the constant that the gradient vector was multiplied by to get to
  // this configuration.  Zero for the starting configuration in a
  // line (set to zero when the gradient is calculated).
  double parameter;

  // What functions/dimensions should be used for this configuration?
  struct functionDefinition *functionDefinition;

  // If caller wants to maintain any configuration dependant state
  // information, it can be saved here.  If this is non-null, the
  // freeExtra() function will be called when this configuration is
  // freed.  Otherwise, this field is not used by the minimizer.
  void *extra;

  // Used to avoid evaluating the function more than once for the same
  // configuration.
  int functionValueValid;

  // A simple reference count garbage collector.
  int referenceCount;
};

struct functionDefinition
{
  // This is the user function that is called to evaluate the
  // potential energy of a configuration.  It should take
  // p->coordinate as it's arguments, and set p->functionValue to the
  // result.
  void (*func)(struct configuration *p);

  // This is the user function that is called to evaluate the gradient
  // of the potential energy function.  It should take p->coordinate
  // as it's arguments, and set p->grandient to the result.  Note that
  // p->gradient is allocated before dfunc is called.  If dfunc is
  // NULL, the gradient will be calculated from the potential
  // function, make sure gradient_delta is set.  Don't do this for
  // high values of dimension!
  void (*dfunc)(struct configuration *p);

  // Called whenever a configuration is freed, if the extra field is
  // non-null.  Set freeExtra to NULL if extra is never used.
  void (*freeExtra)(struct configuration *p);

  // Called from minimize_one_tolerance with the previous and current
  // configurations.  Return non-zero to terminate this tolerance,
  // zero to continue.  If set to NULL, continues until the delta *
  // tolerance is about the average value of the function.
  int (*termination)(struct functionDefinition *fd,
                     struct configuration *previous,
                     struct configuration *current,
                     double tolerance);
  
  // How close do we need to get to the minimum?  Should be no smaller
  // than the square root of the machine precision.  First we minimize
  // to coarse_tolerance, then to fine_tolerance.
  double coarse_tolerance;
  double fine_tolerance;

  // Step size for default calculation of gradient (only used if dfunc
  // is NULL).
  double gradient_delta;

  // How big are the coordinate and gradient arrays?  This is the "N"
  // in N-dimensional above.
  int dimension;

  // When searching for a minimum while bracketing, what should the
  // gradient be initially multiplied by.  Try 1.0 as a wild guess.
  double initial_parameter_guess;

  // How many times have we called (*func)()?
  int functionEvaluationCount;

  // How many times have we called (*dfunc)()?
  int gradientEvaluationCount;

  // Progress messages from the minimizer are reported here.  Allocate
  // a buffer and record it's lengh here, or set messageBufferLength
  // to zero to disable.
  char *message;
  int messageBufferLength;
};

enum minimizationAlgorithm {
  SteepestDescent,
  PolakRibiereConjugateGradient,
  FletcherReevesConjugateGradient
};


extern void initializeFunctionDefinition(struct functionDefinition *fd,
                                         void (*func)(struct configuration *p),
                                         int dimension,
                                         int messageBufferLength);

extern struct configuration *makeConfiguration(struct functionDefinition *fd);

extern void freeConfiguration(struct configuration *conf);

extern void SetConfiguration(struct configuration **dst, struct configuration *src);

extern double evaluate(struct configuration *p);

extern void evaluateGradientFromPotential(struct configuration *p);

extern void evaluateGradient(struct configuration *p);

extern struct configuration *gradientOffset(struct configuration *p, double q);

extern struct configuration *minimize(struct configuration *p, int *iteration, int iterationLimit);

