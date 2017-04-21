<?php 
//modele : Acces au donnes

<<<<<<< HEAD
try
{
	$bdd = new PDO('mysql:host=localhost;dbname=projet_blog_p3;charset=utf8', 'root', 'root');
}
catch (Exception $e)
{
        die('Erreur : ' . $e->getMessage());
}

$query = "SELECT * FROM billets ORDER BY date_creation, name";
$req =$bdd->prepare($query);
$req->execute();

// PDO::FETCH_ASSOC = retourne un tableau indexé par le nom de la colonne comme retourné dans le jeu de résultats

while ($row = $req->fetch(PDO::FETCH_ASSOC)) {
	
	$touslesbillets[] = new Billet($row);
	
;?>
=======
require 'modele/blog/get_billets.php';
>>>>>>> parent of d3aeecf... retour en mode tableau

$billets = get_billets();






	<!DOCTYPE html>
	<html>
	<!-- on récupere le headers  -->


	<?php include_once("header.php"); ?>
		<?php include_once("header.php"); ?> +

			<body>
				<?php include_once("header_top.php"); ?>
					<?php include_once("menu.php"); ?>
						<?php include_once("banner.php"); ?>
							<?php include ("container_corps.php"); ?>
								<?php include_once("footer.php"); ?>
									<?php include ("script.php"); ?>

			</body>


	</html>