interface SkeletonProps {
  count?: number;
}

const SkeletonItem = () => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden animate-pulse">
      {/* Barra superior */}
      <div className="h-1.5 bg-gray-200 w-full" />
      
      <div className="p-5">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-center mb-4">
          <div className="flex items-center">
            <div className="h-4 bg-gray-200 rounded w-32 mb-2 sm:mb-0" />
          </div>
          <div className="h-6 bg-gray-200 rounded-full w-20" />
        </div>
        
        {/* Contenido */}
        <div className="space-y-2 mb-4">
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-3/4" />
        </div>
        
        {/* Etiquetas */}
        <div className="mt-4 flex flex-wrap gap-2">
          <div className="h-6 bg-gray-200 rounded-full w-16" />
          <div className="h-6 bg-gray-200 rounded-full w-20" />
          <div className="h-6 bg-gray-200 rounded-full w-24" />
        </div>
      </div>
    </div>
  );
};

const Skeleton = ({ count = 3 }: SkeletonProps) => {
  return (
    <div className="space-y-6">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonItem key={index} />
      ))}
    </div>
  );
};

export default Skeleton; 