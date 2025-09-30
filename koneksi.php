<?php
    $host="localhost";
    $user="root";
    $pass="";
    $database="stuntfree";
    $koneksi = mysqli_connect($host,$user,$pass,$database);

    if ($koneksi) {
        die("Koneksi Gagal: " . mysqli_connect_error());
    }
?>