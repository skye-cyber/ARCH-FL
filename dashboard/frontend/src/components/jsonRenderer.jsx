export const RenderJSONView = (config) => {
    const formatJSON = (obj, indent = 0) => {
        if (typeof obj !== 'object' || obj === null) {
            return <span className="text-emerald-600 dark:text-emerald-400">"{obj}"</span>;
        }

        if (Array.isArray(obj)) {
            return (
                <span>
                    [<br />
                    {obj.map((item, idx) => (
                        <div key={idx} className="ml-8">
                            {formatJSON(item, indent + 1)}
                            {(obj && idx < obj?.length - 1) ? ',' : ''}
                        </div>
                    ))}
                    <br />
                    {Array(indent * 2).fill('\u00A0').join('')}]
                </span>
            );
        }

        const entries = Object.entries(obj);

        return (
            <span>
                {'{'}<br />
                {entries.map(([key, value], idx) => (
                    <div key={key} className="ml-8">
                        <span className="text-indigo-600 dark:text-indigo-400">"{key}"</span>
                        : {formatJSON(value, indent + 1)}
                        {(entries && idx < entries?.length - 1) || 0 ? ',' : ''}
                    </div>
                ))}
                <br />
                {Array(indent * 2).fill('\u00A0').join('')}{'}'}
            </span>
        );
    };

    return (
        <div className="bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-100 p-6 rounded-xl font-mono text-sm overflow-auto max-h-[500px] scrollbar-custom">
            <pre>{formatJSON(config)}</pre>
        </div>
    );
};
