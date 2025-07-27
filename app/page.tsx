import Link from 'next/link'
import { ArrowRightIcon, ChartBarIcon, DatabaseIcon, BoltIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'

export default function Home() {
  return (
    <div className="relative">
      {/* Hero Section */}
      <div className="bg-gradient-to-b from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-6">
              KROM Analysis Dashboard
            </h1>
            <p className="text-xl mb-8 text-blue-100">
              Advanced analytics and insights for crypto calls from the KROM ecosystem
            </p>
            <Link
              href="/analysis"
              className="inline-flex items-center px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              Open Dashboard
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
            Powerful Analytics at Your Fingertips
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <ChartBarIcon className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Performance Metrics</h3>
              <p className="text-gray-600">
                Track ROI, win rates, and performance across different groups and timeframes
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <DatabaseIcon className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">98,000+ Calls</h3>
              <p className="text-gray-600">
                Comprehensive database of historical crypto calls with detailed metadata
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <BoltIcon className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Real-time Analysis</h3>
              <p className="text-gray-600">
                Interactive charts and filters for instant insights and pattern discovery
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
                <CurrencyDollarIcon className="h-6 w-6 text-yellow-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Smart Filtering</h3>
              <p className="text-gray-600">
                Filter by network, group, time period, and performance to find the best calls
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gray-100 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4 text-gray-900">
            Ready to Analyze?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Dive deep into crypto call performance and discover winning patterns
          </p>
          <Link
            href="/analysis"
            className="inline-flex items-center px-8 py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-lg"
          >
            Launch Dashboard
            <ArrowRightIcon className="ml-2 h-6 w-6" />
          </Link>
        </div>
      </div>
    </div>
  )
}