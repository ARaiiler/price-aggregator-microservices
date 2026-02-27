const jwt = require('jsonwebtoken');

/**
 * JWT Authentication Middleware
 */
const authMiddleware = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: {
          message: 'No token provided',
          status: 401
        }
      });
    }

    const token = authHeader.split(' ')[1];

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Inject user into request
    req.user = decoded;

    next();
  } catch (error) {
    return res.status(403).json({
      error: {
        message: 'Invalid or expired token',
        status: 403
      }
    });
  }
};

module.exports = authMiddleware;