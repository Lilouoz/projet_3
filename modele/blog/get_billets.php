<?php

//retourner un certain nombre de billets depuis la base de données

function get_billets ()
{	
	 try
{
	$bdd = new PDO('mysql:host=localhost;dbname=projet_blog_p3;charset=utf8', 'root', 'root');
}
catch (Exception $e)
{
        die('Erreur : ' . $e->getMessage());
};

 	$billets = $bdd ->query('SELECT id , image, titre , contenu ,auteur, DATE_FOR M AT (date_creation , \'% d/% m /% Y à % Hh % imin % ss\') AS date_creation_fr FROM billets ORDER BY date_creation DESC LIMIT ');

  	return $billets ;
}