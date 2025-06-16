'use client';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  bordered?: boolean;
  hoverable?: boolean;
}

export default function Card({
  className,
  children,
  bordered = true,
  hoverable = true,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-lg p-6',
        bordered && 'border border-gray-200',
        hoverable && 'transition-shadow hover:shadow-md',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
} 