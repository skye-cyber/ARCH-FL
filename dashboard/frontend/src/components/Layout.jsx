import { Outlet, Link } from 'react-router-dom'
import { FaHome, FaFlask, FaProjectDiagram, FaCog } from 'react-icons/fa'
//import { useTheme } from './Themes/useThemeHeadless'
import ThemeToggle from './Themes/useTheme'

const Layout = ({}) => {
    //const { isDark, toggleTheme, setTheme } = useTheme();

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-secondary-900">
            {/* Header */}
            <header className="sticky z-10 top-0 left-0 right-0 w-full bg-white dark:bg-secondary-700 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">ARCH-FL Dashboard</h1>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-sm text-gray-600 dark:text-white">Federated Learning Platform</span>
                            <ThemeToggle />
                        </div>
                    </div>
                </div>
            </header>

            {/* Main content */}
            <div className="max-w-full md:max-w-7xl mx-0 px-2 sm:px-6 py-6">
                <div className="flex flex-col md:flex-row gap-2 sm:gap-6">
                    {/* Sidebar */}
                    <aside className="lg:w-64 flex-shrink-0 dark:text-white">
                        <nav className="sticky z-10 top-24 bg-white dark:bg-accent-600 rounded-lg shadow p-4">
                            <ul className="space-y-2">
                                <li>
                                    <Link
                                        to="/"
                                        className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors"
                                    >
                                        <FaHome className="mr-3" />
                                        <span>Home</span>
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/experiments"
                                        className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors"
                                    >
                                        <FaFlask className="mr-3" />
                                        <span>Experiments</span>
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/architectures"
                                        className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors"
                                    >
                                        <FaProjectDiagram className="mr-3" />
                                        <span>Architectures</span>
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/settings"
                                        className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors"
                                    >
                                        <FaCog className="mr-3" />
                                        <span>Settings</span>
                                    </Link>
                                </li>
                            </ul>
                        </nav>
                    </aside>

                    {/* Content area */}
                    <main className="flex-1">
                        <Outlet />
                    </main>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-white border-t mt-auto py-4">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center text-sm text-gray-500">
                        © {new Date().getFullYear()} ARCH-FL. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    )
}

export default Layout
