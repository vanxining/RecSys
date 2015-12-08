workspace "Similarity"
   configurations { "Debug", "Release" }

    project "Similarity"
        home = ".."

        kind "SharedLib"
        targetdir(home .. "/..")
        targetextension ".pyd"
        targetname "sim"

        files { home .. "/**.h", home .. "/**.c", home .. "/**.cpp" }

        filter "system:Windows"
            pyroot = os.getenv("SystemDrive") .. "/Python27"

            includedirs { pyroot .. "/include" }
            libdirs { pyroot .. "/libs" }
            links { "python27" }

            includedirs { pyroot .. "/Lib/site-packages/numpy/core/include" }
            defines { "NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION" }

        filter "system:Linux"
            includedirs { "" }

        filter "configurations:Debug"
            targetsuffix "_d"

            defines { "DEBUG" }
            flags { "Symbols" }

        filter "configurations:Release"
            defines { "NDEBUG" }
            optimize "On"