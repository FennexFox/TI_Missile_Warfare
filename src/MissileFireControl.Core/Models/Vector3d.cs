using System;

namespace MissileFireControl.Core.Models
{
    public struct Vector3d
    {
        public double X;
        public double Y;
        public double Z;

        public Vector3d(double x, double y, double z)
        {
            X = x;
            Y = y;
            Z = z;
        }

        public static Vector3d Zero { get { return new Vector3d(0, 0, 0); } }

        public double Length()
        {
            return Math.Sqrt(X * X + Y * Y + Z * Z);
        }

        public Vector3d Normalized()
        {
            double length = Length();
            if (length <= 1e-9)
            {
                return Zero;
            }

            return new Vector3d(X / length, Y / length, Z / length);
        }

        public static double Dot(Vector3d left, Vector3d right)
        {
            return left.X * right.X + left.Y * right.Y + left.Z * right.Z;
        }

        public static double Distance(Vector3d left, Vector3d right)
        {
            return (left - right).Length();
        }

        public static Vector3d operator +(Vector3d left, Vector3d right)
        {
            return new Vector3d(left.X + right.X, left.Y + right.Y, left.Z + right.Z);
        }

        public static Vector3d operator -(Vector3d left, Vector3d right)
        {
            return new Vector3d(left.X - right.X, left.Y - right.Y, left.Z - right.Z);
        }

        public static Vector3d operator *(Vector3d value, double scalar)
        {
            return new Vector3d(value.X * scalar, value.Y * scalar, value.Z * scalar);
        }
    }
}
