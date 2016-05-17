workspace "Similarity"
   configurations { "Debug", "Release" }

    project "Similarity"
        home = ".."

        kind "SharedLib"
        targetdir(home .. "/..")
        targetname "sim"

        files { home .. "/**.h", home .. "/**.c", home .. "/**.cpp" }
        defines { "NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION" }

        filter "system:windows"
            targetextension ".pyd"

            sysdrive = os.getenv("SystemDrive")
            if sysdrive == nil then sysdrive = "C:" end
            pyroot = sysdrive .. "/Python27"

            includedirs { pyroot .. "/include" }
            libdirs { pyroot .. "/libs" }
            links { "python27" }

            includedirs { pyroot .. "/Lib/site-packages/numpy/core/include" }

        filter "system:linux"
            targetprefix ""

            buildoptions { "-std=c++11", "`pkg-config python-2.7 --cflags`" }
            links { "python2.7" }

            pylibroot = os.getenv("HOME") .. "/anaconda2/lib/python2.7/site-packages"
            includedirs { pylibroot .. "/numpy/core/include" }

        filter "configurations:Debug"
            targetsuffix "_d"

            defines { "DEBUG" }
            flags { "Symbols" }

        filter "configurations:Release"
            defines { "NDEBUG" }
            optimize "On"
