"use client";
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

type ChartProps = {
    type: 'bar' | 'line' | 'pie';
    data: any[];
    xKey: string;
    yKey: string;
};

const COLORS = ['#E8400C', '#F26335', '#C4320A', '#10b981', '#f59e0b'];

export default function DynamicChart({ type, data, xKey, yKey }: ChartProps) {
    if (!data || data.length === 0) return null;

    const renderChart = () => {
        switch (type) {
            case 'bar':
                return (
                    <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} barSize={24}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                        <XAxis dataKey={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} />
                        <Tooltip cursor={{ fill: '#F3F4F6' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                        <Bar dataKey={yKey} fill="#E8400C" radius={[4, 4, 4, 4]} />
                    </BarChart>
                );
            case 'line':
                return (
                    <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                        <XAxis dataKey={xKey} stroke="#9ca3af" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                        <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} dx={-10} fontSize={12} />
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                        <Line type="monotone" dataKey={yKey} stroke="#E8400C" strokeWidth={3} dot={{ r: 4, fill: '#E8400C', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} />
                    </LineChart>
                );
            case 'pie':
                return (
                    <PieChart margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <Pie data={data} cx="50%" cy="50%" labelLine={false} outerRadius={100} fill="#8884d8" dataKey={yKey} nameKey={xKey}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E5E7EB', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                    </PieChart>
                );
            default:
                return null;
        }
    };

    return (
        <div className="w-full h-[260px] mt-2">
            <ResponsiveContainer width="100%" height="100%">
                {renderChart()}
            </ResponsiveContainer>
        </div>
    );
}