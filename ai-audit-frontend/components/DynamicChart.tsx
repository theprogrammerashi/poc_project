"use client";
import React from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    AreaChart, Area, ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface DynamicChartProps {
    type: 'line' | 'bar' | 'area' | 'scatter' | 'pie' | 'donut';
    data: any[];
    xKey?: string;
    yKey?: string;
    layout?: 'horizontal' | 'vertical';
    scrollable?: boolean;
};

const COLORS = ['#E8400C', '#00639C', '#F7A189', '#63B1E5', '#008298', '#FF6A39', '#8EDCE6', '#2C2C2C'];

export default function DynamicChart({ type, data, xKey = 'name', yKey = 'value', layout = 'horizontal', scrollable = false }: DynamicChartProps) {
    if (!data || data.length <= 1) return null;

    const renderChart = () => {
        switch (type) {
            case 'bar':
                const isHorizontal = layout === 'horizontal';
                return (
                    <BarChart data={data} layout={isHorizontal ? "vertical" : "horizontal"} margin={{ top: 20, right: 20, left: isHorizontal ? 20 : -20, bottom: 0 }} barSize={isHorizontal ? 20 : 32}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={!isHorizontal} horizontal={isHorizontal} />
                        <XAxis type={isHorizontal ? "number" : "category"} dataKey={isHorizontal ? undefined : xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis type={isHorizontal ? "category" : "number"} dataKey={isHorizontal ? xKey : undefined} stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} width={isHorizontal ? 150 : 40} />
                        <Tooltip cursor={{ fill: '#F9FAFB' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Bar dataKey={yKey} radius={isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Bar>
                    </BarChart>
                );
            case 'line':
            case 'area':
                return (
                    <AreaChart data={data} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#E8400C" stopOpacity={0.15}/>
                                <stop offset="95%" stopColor="#E8400C" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={true} />
                        <XAxis dataKey={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Area 
                            type="monotone" 
                            dataKey={yKey} 
                            stroke="#E8400C" 
                            strokeWidth={3} 
                            fill="url(#colorGradient)" 
                            activeDot={{ r: 6, fill: '#E8400C', stroke: '#fff', strokeWidth: 2 }} 
                            dot={{ r: 5, fill: '#E8400C', strokeWidth: 2, stroke: '#fff' }} 
                        />
                    </AreaChart>
                );
            case 'pie':
                return (
                    <PieChart margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <Pie data={data} cx="50%" cy="50%" labelLine={false} outerRadius={100} innerRadius={60} fill="#8884d8" dataKey={yKey} nameKey={xKey} stroke="none" paddingAngle={2} cornerRadius={4}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} itemStyle={{ color: '#1F2937' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                    </PieChart>
                );
            case 'scatter':
                return (
                    <ScatterChart margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={true} />
                        <XAxis type="category" dataKey={xKey} name={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <YAxis type="number" dataKey={yKey} name={yKey} stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} tick={{ fill: '#9ca3af' }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Scatter name={yKey} data={data} fill="#E8400C" shape="circle" />
                    </ScatterChart>
                );
            case 'pie':
            case 'donut':
                const PIE_COLORS = ['#E8400C', '#00639C', '#F7A189', '#63B1E5', '#008298', '#FF6A39', '#8EDCE6'];
                return (
                    <PieChart margin={{ top: 20, right: 20, left: 20, bottom: 20 }}>
                        <Pie
                            data={data}
                            innerRadius={type === 'donut' ? 60 : 0}
                            outerRadius={100}
                            paddingAngle={type === 'donut' ? 3 : 0}
                            dataKey={yKey as string}
                            nameKey={xKey as string}
                            cx="50%"
                            cy="50%"
                            label={({ name, percent }) => percent !== undefined ? `${name} ${(percent * 100).toFixed(0)}%` : name}
                            labelLine={true}
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip cursor={{ fill: '#F9FAFB' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    </PieChart>
                );
            default:
                return null;
        }
    };

    const [mounted, setMounted] = React.useState(false);
    React.useEffect(() => setMounted(true), []);

    if (!mounted) {
        return <div className="w-full h-[260px] mt-2 bg-gray-50/50 animate-pulse rounded-xl" />;
    }

    const chartHeight = scrollable ? Math.max(260, data.length * 40) : '100%';

    return (
        <div className={`w-full ${scrollable ? 'overflow-y-auto custom-scrollbar' : ''}`} style={{ height: '260px' }}>
            <div style={{ height: chartHeight, width: '100%', minHeight: '260px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    {renderChart()}
                </ResponsiveContainer>
            </div>
        </div>
    );
}