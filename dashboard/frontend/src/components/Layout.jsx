import { useRef } from "react";
import { Outlet, Link } from "react-router-dom";
import { FaHome, FaFlask, FaProjectDiagram, FaCog } from "react-icons/fa";

export default function Layout() {
    const mobileMenu = useRef(null)
    const mobileMenuShow = () => {
        mobileMenu.current.classList.remove('hidden')
    }
    const mobileMenuHide = () => {
        mobileMenu.current.classList.add('hidden')
    }
    const mobileMenuToggle=()=>{
      mobileMenu.current.classList.toggle('hidden')
    }
    return (
        <div className="min-h-screen h-screen bg-gray-50 overflow-x-hidden">
            {/* Header */}

            <header className="sticky top-0 left-0 w-full z-[30] bg-white shadow-sm py-2">
                {/*For small screen */}
                <button onClick={mobileMenuToggle} className="absolute md:hidden top-3 left-0 z-[31] hover:bg-gray-200 dark:hover:bg-gray-100 p-1 size-10 rounded-full transition-colors duration-700 flex items-center justify-center">
                    <div className="space-y-1">
                        <p className="px-2.5 py-[1px] bg-gray-700 dark:bg-gray-300"></p>
                        <p className="px-2.5 py-[1px] bg-gray-700 dark:bg-gray-300"></p>
                        <p className="px-2.5 py-[1px] bg-gray-700 dark:bg-gray-300"></p>
                    </div>
                </button>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 ml-8 md:ml-0">
                    <div className="relative flex lg:justify-between items-center">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-primary flex gap-2">
                                ARCH-FL <span className="hidden lg:flex">Dashboard</span>
                            </h1>
                        </div>
                        <nav className="hidden md:flex rounded-lg p-1">
                            <div>
                                <Link
                                    to="/"
                                    className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors text-md"
                                >
                                    <FaHome className="mr-3" />
                                    <span>Home</span>
                                </Link>
                            </div>
                            <div>
                                <Link
                                    to="/experiments"
                                    className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors text-md"
                                >
                                    <FaFlask className="mr-3" />
                                    <span>Experiments</span>
                                </Link>
                            </div>
                            <div>
                                <Link
                                    to="/architectures"
                                    className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors text-md"
                                >
                                    <FaProjectDiagram className="mr-3" />
                                    <span>Architectures</span>
                                </Link>
                            </div>
                            <div>
                                <Link
                                    to="/settings"
                                    className="flex items-center px-3 py-2 text-gray-700 rounded-md hover:bg-gray-100 hover:text-primary transition-colors text-md"
                                >
                                    <FaCog className="mr-3" />
                                    <span>Settings</span>
                                </Link>
                            </div>
                        </nav>
                        <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600 hidden lg:flex">
                                Federated Learning Platform
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main content */}
            <div className="max-w-full mx-auto px-2 sm:px-6 py-6">
                <div className="flex flex-cols lg:flex-row gap-4">
                    {/* Sidebar */}
                    <aside onMouseLeave={mobileMenuHide} ref={mobileMenu} className="hidden absolute z-[31] top-12 left-0 bg-white shadow-md block lg:w-62">
                        <nav className="bg-white rounded-lg shadow p-4">
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
    );
}
