/**
 * Request Validator Middleware
 * Purpose: Validate incoming request data using Joi schemas
 */
import { Request, Response, NextFunction } from 'express'
import Joi from 'joi'
import { createError } from './errorHandler'

export const validateRequest = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.body)
    
    if (error) {
      const errorMessage = error.details.map(detail => detail.message).join(', ')
      return next(createError(errorMessage, 400))
    }
    
    next()
  }
}
